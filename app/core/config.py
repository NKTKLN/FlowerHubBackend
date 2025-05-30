"""Модуль конфигурации приложения.

Содержит класс Config для загрузки настроек из переменных окружения.
Позволяет управлять параметрами базы данных, пагинацией и внешними ресурсами.
"""

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    # Настройки хеширования паролей
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Настройки Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int

    # Настройки PostgreSQL
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    @property
    def POSTGRES_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Конфигурация загрузки переменных окружения
    model_config = ConfigDict(env_file=".env")  # type: ignore
    _ = model_config  # type: ignore


# Единственный экземпляр конфигурации, используемый в приложении
config: Config = Config()  # type: ignore[call-arg]
