import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

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
    get_orders_by_seller,
    get_user_by_id,
    update_flower,
)
from app.crud.order import get_order_by_id
from app.db import get_session
from app.schemas import (
    FlowerCountryCreate,
    FlowerCreate,
    FlowerData,
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
)

logger = logging.getLogger(__name__)


class SellerAPI:
    def __init__(self):
        self.router = APIRouter()

        self.router.post("/flowers", response_model=FlowerData)(self.add_flower)
        self.router.put("/flowers/{flower_id}", response_model=FlowerData)(self.edit_flower)
        self.router.delete("/flowers/{flower_id}")(self.remove_flower)
        self.router.get("/orders", response_model=List[OrderSchema])(self.get_orders)
        self.router.put("/change_order_status", response_model=list[OrderResponse])(self.change_order_status)

    async def change_order_status(
        self,
        order_id: int,
        user_id: int = Depends(verify_token),
        db: AsyncSession = Depends(get_session),
    ):
        logger.info(f"Пользователь {user_id} пытается изменить статус заказа {order_id}")
        user = await get_user_by_id(db, user_id)
        if not user or not (user.is_user_seller or user.is_user_admin):
            logger.warning(
                f"Доступ запрещён пользователю {user_id} для изменения статуса заказа — не продавец или админ"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ разрешён только продавцам и администраторам",
            )

        order = await get_order_by_id(db, order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Заказ не найден",
            )

        order.is_closed = not order.is_closed
        db.add(order)
        await db.commit()
        await db.refresh(order)

        logger.info(f"Статус заказа {order_id} изменён на {'закрыт' if order.is_closed else 'открыт'}")
        return {"detail": "Данные заказа успешно обновлены"}

    async def add_flower(
        self,
        flower_data: FlowerCreate,
        user_id: int = Depends(verify_token),
        db: AsyncSession = Depends(get_session),
    ):
        logger.info(f"Пользователь {user_id} пытается добавить цветок")
        user = await get_user_by_id(db, user_id)
        if not user or not (user.is_user_seller or user.is_user_admin):
            logger.warning(f"Доступ запрещён для пользователя {user_id}: не продавец")
            raise HTTPException(status_code=403, detail="Доступ разрешен только продавцам")
        flower = await create_flower(db, flower_data)
        await add_flower_to_seller(db, flower.id, user_id)
        logger.info(f"Цветок добавлен пользователем {user_id}, ID цветка: {flower.id}")
        return flower

    async def edit_flower(
        self,
        flower_id: int,
        flower_data: FlowerUpdate,
        user_id: int = Depends(verify_token),
        db: AsyncSession = Depends(get_session),
    ):
        logger.info(f"Пользователь {user_id} пытается изменить цветок ID {flower_id}")
        user = await get_user_by_id(db, user_id)
        if not user or not (user.is_user_seller or user.is_user_admin):
            logger.warning(f"Доступ запрещён для пользователя {user_id}: не продавец")
            raise HTTPException(status_code=403, detail="Доступ разрешен только продавцам")
        updated_flower = await update_flower(db, flower_id, flower_data)
        logger.info(f"Цветок ID {flower_id} обновлён пользователем {user_id}")
        return updated_flower

    async def remove_flower(
        self,
        flower_id: int,
        user_id: int = Depends(verify_token),
        db: AsyncSession = Depends(get_session),
    ):
        logger.info(f"Пользователь {user_id} пытается удалить цветок ID {flower_id}")
        user = await get_user_by_id(db, user_id)
        if not user or not (user.is_user_seller or user.is_user_admin):
            logger.warning(f"Доступ запрещён для пользователя {user_id}: не продавец")
            raise HTTPException(status_code=403, detail="Доступ разрешен только продавцам")
        await delete_flower(db, flower_id)
        logger.info(f"Цветок ID {flower_id} удалён пользователем {user_id}")
        return {"detail": "Цветок удалён успешно"}

    async def get_orders(
        self,
        user_id: int = Depends(verify_token),
        db: AsyncSession = Depends(get_session),
    ):
        logger.info(f"Пользователь {user_id} запрашивает свои заказы")
        user = await get_user_by_id(db, user_id)
        if not user or not (user.is_user_seller or user.is_user_admin):
            logger.warning(f"Доступ запрещён для пользователя {user_id}: не покупатель")
            raise HTTPException(403, "Доступ разрешен только покупателям")

        orders = await get_orders_by_seller(db, user_id)
        logger.info(f"Пользователь {user_id} получил {len(orders)} заказов")
        return orders
