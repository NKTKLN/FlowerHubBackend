"""Модуль для работы с асинхронной базой данных.

Содержит настройки подключения к базе данных, объявление асинхронной сессии,
базового класса для ORM-моделей, а также функции инициализации БД и получения сессии.
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Инициализация логгера
logger = logging.getLogger(__name__)

# Создание асинхронного движка SQLAlchemy
engine = create_async_engine("sqlite+aiosqlite:///flowers.db")  # TODO: заменить на config.DB_URL

# Создание фабрики асинхронных сессий
async_session = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

# Базовый класс для декларативных ORM-моделей
Base = declarative_base()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Получить асинхронную сессию для работы с базой данных.

    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy.
    """
    async with async_session() as session:
        yield session


async def init_db() -> None:
    """Инициализировать базу данных, создав все таблицы, определённые в моделях.

    Эта функция использует метаданные из Base и создаёт все таблицы,
    если они ещё не существуют.

    Raises:
        Любые исключения, возникающие при подключении к БД или выполнении запросов.
    """
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # type: ignore[attr-defined]
    logger.info("Database tables created.")
