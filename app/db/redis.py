import redis

from app.core.config import config

# Настройки Redis
redis_client = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=config.REDIS_DB,
    decode_responses=True,  # если нужны строки, а не байты
)
