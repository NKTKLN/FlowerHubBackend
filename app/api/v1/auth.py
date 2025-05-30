import logging
from datetime import timedelta

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core import auth_service, config, verify_token
from app.crud import create_user, get_user_by_email
from app.db import get_session
from app.schemas import RefreshTokenRequest, TokenResponse, UserLogin, UserRegister

logger: logging.Logger = logging.getLogger(__name__)


class AuthAPI:
    def __init__(self):
        self.router = APIRouter()

        # Регистрация маршрутов
        self.router.post("/login", response_model=TokenResponse)(self.login)
        self.router.post("/refresh", response_model=TokenResponse)(self.refresh_token)
        self.router.post("/register", response_model=TokenResponse)(self.register_user)
        self.router.post("/check-token")(self.check_token)

    async def check_token(self, _: str = Depends(verify_token)):
        return {"detail": "Токен активен"}

    async def register_user(self, user_data: UserRegister, db: Session = Depends(get_session)):
        logger.info("Начало регистрации пользователя с email: %s", user_data.email)

        existing_user = await get_user_by_email(db, user_data.email)
        if existing_user:
            logger.warning("Попытка регистрации с существующим email: %s", user_data.email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        user = await create_user(db, user_data)
        logger.info("Пользователь успешно создан: ID %s", user.id)

        access_token = auth_service.create_access_token(user.id)
        refresh_token = auth_service.create_refresh_token(user.id)

        logger.info("Токены успешно сгенерированы для пользователя ID %s", user.id)

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def login(self, user_data: UserLogin, db: Session = Depends(get_session)):
        logger.info("Попытка входа для пользователя: %s", user_data.email)

        user = await get_user_by_email(db, user_data.email)
        if not user:
            logger.warning("Неудачная попытка входа: пользователь не найден - %s", user_data.email)
            raise HTTPException(status_code=400, detail="Incorrect username or password")

        if not auth_service.verify_password(user_data.password, user.password_hash):
            logger.warning("Неудачная попытка входа: неверный пароль для %s", user_data.email)
            raise HTTPException(status_code=400, detail="Incorrect username or password")

        access_token = auth_service.create_access_token(user.id)
        refresh_token = auth_service.create_refresh_token(user.id)

        logger.info("Успешный вход для пользователя ID %s. Токены сгенерированы.", user.id)

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def refresh_token(self, token_data: RefreshTokenRequest = Body(...)):
        logger.info("Получен запрос на обновление токена")

        payload = auth_service.decode_token(token_data.refresh_token)
        if not payload:
            logger.error("Невалидный refresh токен")
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        if auth_service.is_token_revoked(token_data.refresh_token):
            logger.warning("Попытка использовать отозванный refresh токен")
            raise HTTPException(status_code=401, detail="Token revoked")

        user_id = payload.get("sub")
        if not user_id:
            logger.error("Токен не содержит идентификатор пользователя")
            raise HTTPException(status_code=401, detail="Invalid token payload")

        logger.info("Генерация новых токенов для пользователя ID %s", user_id)

        access_token = auth_service.create_access_token(int(user_id))
        new_refresh_token = auth_service.create_refresh_token(int(user_id))

        # Отзываем старый refresh токен
        auth_service.revoke_token(
            token_data.refresh_token, expires_in=timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)
        )

        logger.info("Старый refresh токен отозван. Выданы новые токены.")

        return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)
