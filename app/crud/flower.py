import logging
from typing import List

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models import (
    Country,
    Flower,
    FloweringSeason,
    FlowerType,
    FlowerUsage,
    Person,
    saleable_flowers,
)
from app.schemas import (
    FlowerCountryCreate,
    FlowerCreate,
    FlowerFilter,
    FloweringSeasonCreate,
    FlowerTypeCreate,
    FlowerUpdate,
    FlowerUsageCreate,
)
from app.schemas.flower import FlowerData

logger = logging.getLogger(__name__)


async def get_flowers(
    db: AsyncSession,
    filters: FlowerFilter,
    limit: int = 100,
    offset: int = 0,
) -> List[FlowerData]:
    logger.info(
        f"Получение списка цветов с фильтрами: {filters.dict()}, limit={limit}, offset={offset}"
    )
    query = select(Flower).options(joinedload(Flower.sellers))

    if filters.name:
        query = query.filter(Flower.name.ilike(f"%{filters.name}%"))
    if filters.type_id:
        query = query.filter(Flower.type_id == filters.type_id)
    if filters.id:
        query = query.filter(Flower.id == filters.id)
    if filters.season_id:
        query = query.filter(Flower.season_id == filters.season_id)
    if filters.usage_id:
        query = query.filter(Flower.usage_id == filters.usage_id)
    if filters.country_id:
        query = query.filter(Flower.country_id == filters.country_id)
    if filters.min_price:
        query = query.filter(Flower.price >= filters.min_price)
    if filters.max_price:
        query = query.filter(Flower.price <= filters.max_price)
    if filters.seller_id:
        query = query.join(Flower.sellers).filter(Person.id == filters.seller_id)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    flowers = result.unique().scalars().all()
    logger.info(f"Найдено цветов: {len(flowers)}")

    flower_data_list = [
        FlowerData(
            id=flower.id,
            name=flower.name,
            type_id=flower.type_id,
            season_id=flower.season_id,
            usage_id=flower.usage_id,
            variety=flower.variety,
            price=flower.price,
            country_id=flower.country_id,
            seller_ids=[seller.id for seller in flower.sellers],
        )
        for flower in flowers
    ]

    return flower_data_list


async def add_flower_to_seller(db: AsyncSession, flower_id: int, seller_id: int):
    logger.info(f"Связка цветка {flower_id} с продавцом {seller_id}")
    insert_stmt = saleable_flowers.insert().values(seller_id=seller_id, flower_id=flower_id)
    await db.execute(insert_stmt)
    await db.commit()
    logger.info("Связка создана")


async def create_flower(db: AsyncSession, flower_data: FlowerCreate) -> Flower:
    logger.info(f"Создание нового цветка с данными: {flower_data.dict()}")
    flower = Flower(**flower_data.dict())
    db.add(flower)
    await db.commit()
    await db.refresh(flower)
    logger.info(f"Цветок создан с ID: {flower.id}")
    return flower


async def update_flower(db: AsyncSession, flower_id: int, flower_data: FlowerUpdate) -> Flower:
    logger.info(
        f"Обновление цветка с ID {flower_id} данными: {flower_data.dict(exclude_unset=True)}"
    )
    result = await db.execute(select(Flower).filter_by(id=flower_id))
    flower = result.scalars().first()
    if not flower:
        logger.warning(f"Цветок с ID {flower_id} не найден для обновления")
        raise HTTPException(status_code=404, detail="Цветок не найден")

    for field, value in flower_data.dict(exclude_unset=True).items():
        setattr(flower, field, value)

    await db.commit()
    await db.refresh(flower)
    logger.info(f"Цветок с ID {flower_id} успешно обновлен")
    return flower


async def delete_flower(db: AsyncSession, flower_id: int) -> None:
    logger.info(f"Удаление цветка с ID {flower_id}")
    result = await db.execute(select(Flower).filter_by(id=flower_id))
    flower = result.scalars().first()
    if not flower:
        logger.warning(f"Цветок с ID {flower_id} не найден для удаления")
        raise HTTPException(status_code=404, detail="Цветок не найден")
    await db.delete(flower)
    await db.commit()
    logger.info(f"Цветок с ID {flower_id} успешно удалён")


async def create_flower_type(db: AsyncSession, data: FlowerTypeCreate) -> FlowerType:
    flower_type = FlowerType(**data.dict())
    db.add(flower_type)
    await db.commit()
    await db.refresh(flower_type)
    return flower_type


async def create_flowering_season(db: AsyncSession, data: FloweringSeasonCreate) -> FloweringSeason:
    season = FloweringSeason(**data.dict())
    db.add(season)
    await db.commit()
    await db.refresh(season)
    return season


async def create_flower_usage(db: AsyncSession, data: FlowerUsageCreate) -> FlowerUsage:
    usage = FlowerUsage(**data.dict())
    db.add(usage)
    await db.commit()
    await db.refresh(usage)
    return usage


async def get_flower_types(db: AsyncSession) -> List[FlowerType]:
    result = await db.execute(select(FlowerType))
    return result.scalars().all()


async def get_flowering_seasons(db: AsyncSession) -> List[FloweringSeason]:
    result = await db.execute(select(FloweringSeason))
    return result.scalars().all()


async def get_flower_usages(db: AsyncSession) -> List[FlowerUsage]:
    result = await db.execute(select(FlowerUsage))
    return result.scalars().all()


async def get_flowering_countries(db: AsyncSession) -> List[Country]:
    result = await db.execute(select(Country))
    return result.scalars().all()


async def create_flowering_countries(db: AsyncSession, data: FlowerCountryCreate) -> Country:
    flower_country = Country(**data.dict())
    db.add(flower_country)
    await db.commit()
    await db.refresh(flower_country)
    return flower_country


async def delete_flower_type(db: AsyncSession, flower_type_id: int) -> None:
    logger.info(f"Удаление типа цветка с ID {flower_type_id}")
    result = await db.execute(select(FlowerType).filter_by(id=flower_type_id))
    flower_type = result.scalars().first()
    if not flower_type:
        logger.warning(f"Тип цветка с ID {flower_type_id} не найден для удаления")
        raise HTTPException(status_code=404, detail="Тип цветка не найден")
    await db.delete(flower_type)
    await db.commit()
    logger.info(f"Тип цветка с ID {flower_type_id} успешно удалён")


async def delete_flower_season(db: AsyncSession, flower_season_id: int) -> None:
    logger.info(f"Удаление сезона цветения с ID {flower_season_id}")
    result = await db.execute(select(FloweringSeason).filter_by(id=flower_season_id))
    flower_season = result.scalars().first()
    if not flower_season:
        logger.warning(f"Сезон цветения с ID {flower_season_id} не найден для удаления")
        raise HTTPException(status_code=404, detail="Сезон цветения не найден")
    await db.delete(flower_season)
    await db.commit()
    logger.info(f"Сезон цветения с ID {flower_season_id} успешно удалён")


async def delete_flower_usage(db: AsyncSession, flower_usage_id: int) -> None:
    logger.info(f"Удаление использования цветка с ID {flower_usage_id}")
    result = await db.execute(select(FlowerUsage).filter_by(id=flower_usage_id))
    flower_usage = result.scalars().first()
    if not flower_usage:
        logger.warning(f"Использование цветка с ID {flower_usage_id} не найдено для удаления")
        raise HTTPException(status_code=404, detail="Использование цветка не найдено")
    await db.delete(flower_usage)
    await db.commit()
    logger.info(f"Использование цветка с ID {flower_usage_id} успешно удалено")


async def delete_flower_country(db: AsyncSession, flower_country_id: int) -> None:
    logger.info(f"Удаление страны цветка с ID {flower_country_id}")
    result = await db.execute(select(Country).filter_by(id=flower_country_id))
    flower_country = result.scalars().first()
    if not flower_country:
        logger.warning(f"Страна цветка с ID {flower_country_id} не найдена для удаления")
        raise HTTPException(status_code=404, detail="Страна цветка не найдена")
    await db.delete(flower_country)
    await db.commit()
    logger.info(f"Страна цветка с ID {flower_country_id} успешно удалена")
