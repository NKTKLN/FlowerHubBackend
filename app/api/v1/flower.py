import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core import verify_token
from app.crud import (
    add_flower_to_seller,
    create_flower,
    create_flower_type,
    create_flower_usage,
    create_flowering_countries,
    create_flowering_season,
    delete_flower,
    delete_flower_country,
    delete_flower_season,
    delete_flower_type,
    delete_flower_usage,
    get_flower_types,
    get_flower_usages,
    get_flowering_countries,
    get_flowering_seasons,
    get_flowers,
    get_orders_by_seller,
    get_user_by_id,
    update_flower,
    update_password,
    update_user,
)
from app.db import get_session
from app.schemas import (
    FlowerCountryCreate,
    FlowerCreate,
    FlowerData,
    FlowerFilter,
    FloweringcountriesData,
    FloweringSeasonCreate,
    FloweringSeasonData,
    FlowerTypeCreate,
    FlowerTypeData,
    FlowerUpdate,
    FlowerUsageCreate,
    FlowerUsageData,
    OrderResponse,
    OrderSchema,
    UserData,
)

logger: logging.Logger = logging.getLogger(__name__)


class FlowerAPI:
    def __init__(self):
        self.router = APIRouter()

        # Регистрация маршрутов
        self.router.get("/", response_model=List[FlowerData])(self.list_flowers)
        self.router.post("/types")(self.create_flower_type)
        self.router.post("/seasons")(self.create_flowering_season)
        self.router.post("/usages")(self.create_flower_usage)
        self.router.get("/types", response_model=List[FlowerTypeData])(self.list_flower_types)
        self.router.get("/seasons", response_model=List[FloweringSeasonData])(
            self.list_flowering_seasons
        )
        self.router.get("/usages", response_model=List[FlowerUsageData])(self.list_flower_usages)
        self.router.get("/countries", response_model=List[FloweringcountriesData])(
            self.list_flowering_countries
        )
        self.router.post("/countries")(self.create_flower_countries)
        self.router.delete("/countries/{country_id}")(self.remove_flower_countries)
        self.router.delete("/types/{type_id}")(self.remove_flower_types)
        self.router.delete("/seasons/{season_id}")(self.remove_flower_seasons)
        self.router.delete("/usages/{usage_id}")(self.remove_flower_usages)

    async def list_flower_types(self, db: AsyncSession = Depends(get_session)):
        return await get_flower_types(db)

    async def list_flowering_seasons(self, db: AsyncSession = Depends(get_session)):
        return await get_flowering_seasons(db)

    async def list_flower_usages(self, db: AsyncSession = Depends(get_session)):
        return await get_flower_usages(db)

    async def list_flowering_countries(self, db: AsyncSession = Depends(get_session)):
        return await get_flowering_countries(db)

    async def remove_flower_types(
        self,
        type_id: int,
        user_id: int = Depends(verify_token),
        db: AsyncSession = Depends(get_session),
    ):
        logger.info(f"Пользователь {user_id} пытается удалить тип цветка ID {type_id}")
        user = await get_user_by_id(db, user_id)
        if not user or not (user.is_user_seller or user.is_user_admin):
            logger.warning(f"Доступ запрещён для пользователя {user_id}: не продавец")
            raise HTTPException(status_code=403, detail="Доступ разрешен только продавцам")
        await delete_flower_type(db, type_id)
        logger.info(f"Тип цветка ID {type_id} удалён пользователем {user_id}")
        return {"detail": "Тип цветка удалён успешно"}

    async def remove_flower_seasons(
        self,
        season_id: int,
        user_id: int = Depends(verify_token),
        db: AsyncSession = Depends(get_session),
    ):
        logger.info(f"Пользователь {user_id} пытается удалить сезон цветка ID {season_id}")
        user = await get_user_by_id(db, user_id)
        if not user or not (user.is_user_seller or user.is_user_admin):
            logger.warning(f"Доступ запрещён для пользователя {user_id}: не продавец")
            raise HTTPException(status_code=403, detail="Доступ разрешен только продавцам")
        await delete_flower_season(db, season_id)
        logger.info(f"Сезон цветка ID {season_id} удалён пользователем {user_id}")
        return {"detail": "Сезон цветка удалён успешно"}

    async def remove_flower_usages(
        self,
        usage_id: int,
        user_id: int = Depends(verify_token),
        db: AsyncSession = Depends(get_session),
    ):
        logger.info(f"Пользователь {user_id} пытается удалить использование цветка ID {usage_id}")
        user = await get_user_by_id(db, user_id)
        if not user or not (user.is_user_seller or user.is_user_admin):
            logger.warning(f"Доступ запрещён для пользователя {user_id}: не продавец")
            raise HTTPException(status_code=403, detail="Доступ разрешен только продавцам")
        await delete_flower_usage(db, usage_id)
        logger.info(f"Использование цветка ID {usage_id} удалено пользователем {user_id}")
        return {"detail": "Использование цветка удалено успешно"}

    async def remove_flower_countries(
        self,
        country_id: int,
        user_id: int = Depends(verify_token),
        db: AsyncSession = Depends(get_session),
    ):
        logger.info(f"Пользователь {user_id} пытается удалить страну цветка ID {country_id}")
        user = await get_user_by_id(db, user_id)
        if not user or not (user.is_user_seller or user.is_user_admin):
            logger.warning(f"Доступ запрещён для пользователя {user_id}: не продавец")
            raise HTTPException(status_code=403, detail="Доступ разрешен только продавцам")
        await delete_flower_country(db, country_id)
        logger.info(f"Страна цветка ID {country_id} удалена пользователем {user_id}")
        return {"detail": "Страна цветка удалена успешно"}

    async def create_flower_countries(
        self,
        data: FlowerCountryCreate,
        user_id: int = Depends(verify_token),
        db: AsyncSession = Depends(get_session),
    ):
        user = await get_user_by_id(db, user_id)
        if not user or not (user.is_user_seller or user.is_user_admin):
            logger.warning(f"Доступ запрещён для пользователя {user_id}: не продавец")
            raise HTTPException(status_code=403, detail="Доступ разрешен только продавцам")
        flower_country = await create_flowering_countries(db, data)
        return flower_country

    async def create_flower_type(
        self,
        data: FlowerTypeCreate,
        user_id: int = Depends(verify_token),
        db: AsyncSession = Depends(get_session),
    ):
        user = await get_user_by_id(db, user_id)
        if not user or not (user.is_user_seller or user.is_user_admin):
            logger.warning(f"Доступ запрещён для пользователя {user_id}: не продавец")
            raise HTTPException(status_code=403, detail="Доступ разрешен только продавцам")
        flower_type = await create_flower_type(db, data)
        return flower_type

    async def create_flowering_season(
        self,
        data: FloweringSeasonCreate,
        user_id: int = Depends(verify_token),
        db: AsyncSession = Depends(get_session),
    ):
        user = await get_user_by_id(db, user_id)
        if not user or not (user.is_user_seller or user.is_user_admin):
            logger.warning(f"Доступ запрещён для пользователя {user_id}: не продавец")
            raise HTTPException(status_code=403, detail="Доступ разрешен только продавцам")
        season = await create_flowering_season(db, data)
        return season

    async def create_flower_usage(
        self,
        data: FlowerUsageCreate,
        user_id: int = Depends(verify_token),
        db: AsyncSession = Depends(get_session),
    ):
        user = await get_user_by_id(db, user_id)
        if not user or not (user.is_user_seller or user.is_user_admin):
            logger.warning(f"Доступ запрещён для пользователя {user_id}: не продавец")
            raise HTTPException(status_code=403, detail="Доступ разрешен только продавцам")
        usage = await create_flower_usage(db, data)
        return usage

    async def list_flowers(
        self,
        name: Optional[str] = Query(None),
        flower_id: Optional[int] = Query(None),
        type_id: Optional[int] = Query(None),
        season_id: Optional[int] = Query(None),
        usage_id: Optional[int] = Query(None),
        country_id: Optional[int] = Query(None),
        min_price: Optional[float] = Query(None),
        max_price: Optional[float] = Query(None),
        seller_id: Optional[int] = Query(None),
        limit: int = Query(100, le=100),
        offset: int = Query(0, ge=0),
        db: AsyncSession = Depends(get_session),
    ):
        try:
            logger.info(
                f"Запрос списка цветов с фильтрами: "
                f"name={name}, type_id={type_id}, season_id={season_id}, usage_id={usage_id}, "
                f"country_id={country_id}, min_price={min_price}, max_price={max_price}, "
                f"limit={limit}, offset={offset}, seller_id={seller_id}, flower_id={flower_id}"
            )

            filters = FlowerFilter(
                id=flower_id,
                name=name,
                type_id=type_id,
                season_id=season_id,
                usage_id=usage_id,
                country_id=country_id,
                min_price=min_price,
                max_price=max_price,
                seller_id=seller_id,
            )
            flowers = await get_flowers(db, filters, limit=limit, offset=offset)

            logger.info(f"Найдено {len(flowers)} цветов по запросу")
            return flowers
        except Exception:
            raise HTTPException(status_code=500, detail="Internal server error")
