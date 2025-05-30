import logging
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import config
from app.db.redis import redis_client

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = config.SECRET_KEY
        self.algorithm = config.ALGORITHM
        self.access_token_expire_minutes = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
        self.refresh_token_expire_days = timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)
        self.redis = redis_client

    def get_password_hash(self, password: str) -> str:
        hashed = self.pwd_context.hash(password)
        logger.debug("Пароль успешно захеширован")
        return hashed

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        valid = self.pwd_context.verify(plain_password, hashed_password)
        logger.debug(f"Проверка пароля: {'успешно' if valid else 'неудачно'}")
        return valid

    def create_access_token(self, user_id: int) -> str:
        expire = datetime.now(timezone.utc) + self.access_token_expire_minutes
        to_encode = {"sub": str(user_id), "exp": expire}
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        logger.info(f"Создан access токен для пользователя с id={user_id}")
        return token

    def create_refresh_token(self, user_id: int) -> str:
        expire = datetime.now(timezone.utc) + self.refresh_token_expire_days
        to_encode = {"sub": str(user_id), "exp": expire}
        token = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        self.redis.setex(f"refresh_token:{token}", self.refresh_token_expire_days, user_id)
        logger.info(f"Создан refresh токен и сохранён в Redis для пользователя с id={user_id}")
        return token

    def revoke_token(self, token: str, expires_in: int):
        self.redis.setex(f"blacklist:{token}", expires_in, "true")
        logger.info(f"Токен занесён в черный список на {expires_in} секунд")

    def is_token_revoked(self, token: str) -> bool:
        revoked = self.redis.exists(f"blacklist:{token}") == 1
        logger.debug(f"Проверка, занесён ли токен в черный список: {'да' if revoked else 'нет'}")
        return revoked

    def decode_token(self, token: str):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            logger.debug(f"Токен успешно декодирован, sub={payload.get('sub')}")
            return payload
        except JWTError as e:
            logger.warning(f"Ошибка декодирования токена: {e}")
            return None


auth_service = AuthService()
