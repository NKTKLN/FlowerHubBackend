import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import verify_token
from app.crud import get_user_by_id
from app.crud.order import create_order_by_buyer, get_order_by_id, get_orders_by_buyer
from app.db import get_session
from app.db.models import Flower, Order, ordered_flowers, saleable_flowers
from app.schemas import CreateOrder, OrderResponse

logger = logging.getLogger(__name__)


class OrderAPI:
    def __init__(self):
        self.router = APIRouter()

        self.router.post("/")(self.make_order)
        self.router.get("/orders", response_model=list[OrderResponse])(self.get_my_orders)
        self.router.get("/orders/{order_id}", response_model=OrderResponse)(self.get_order_details)

    async def get_order_details(
        self,
        order_id: int,
        user_id: int = Depends(verify_token),
        db: AsyncSession = Depends(get_session),
    ):
        logger.info(f"Пользователь {user_id} запрашивает детали заказа {order_id}")
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ разрешён только покупателям",
            )

        # Получить заказ
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()

        if not order or (
            str(order.buyer_id) != user_id and not (user.is_user_seller or user.is_user_admin)
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Заказ не найден",
            )

        # Получить список цветов в заказе + количество
        result = await db.execute(
            select(ordered_flowers.c.flower_id, ordered_flowers.c.quantity, Flower)
            .join(Flower, Flower.id == ordered_flowers.c.flower_id)
            .where(ordered_flowers.c.order_id == order_id)
        )
        rows = result.fetchall()

        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товары в заказе не найдены",
            )

        items = []
        seller_id = None

        for flower_id, quantity, flower in rows:
            items.append(
                {
                    "flower_id": flower_id,
                    "quantity": quantity,
                }
            )
            # Предполагаем, что первый продавец — это seller
            result = await db.execute(
                select(saleable_flowers.c.seller_id).where(
                    saleable_flowers.c.flower_id == flower_id
                )
            )
            seller_row = result.first()
            seller_id = seller_row.seller_id if seller_row else None

        return OrderResponse(
            buyer_id=order.buyer_id,
            order_id=order.id,
            seller_id=seller_id,
            order_date=order.order_date,
            is_closed=order.is_closed,
            items=items,
        )

    async def make_order(
        self,
        order_data: CreateOrder,
        user_id: int = Depends(verify_token),
        db: AsyncSession = Depends(get_session),
    ):
        logger.info(f"Пользователь {user_id} пытается создать заказ: {order_data}")
        user = await get_user_by_id(db, user_id)
        if not user or user.is_user_seller:
            logger.warning(
                f"Доступ запрещён пользователю {user_id} для создания заказа — не покупатель"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ разрешён только покупателям",
            )

        orders = await create_order_by_buyer(
            db, user_id, [item.dict() for item in order_data.items]
        )
        logger.info(
            f"Заказ(ы) успешно создан(ы) для пользователя {user_id}, количество: {len(orders)}"
        )
        return {"details": "Заказ оформлен успешно"}

    async def get_my_orders(
        self,
        user_id: int = Depends(verify_token),
        db: AsyncSession = Depends(get_session),
    ):
        logger.info(f"Пользователь {user_id} запрашивает свои заказы")
        user = await get_user_by_id(db, user_id)
        if not user or user.is_user_seller:
            logger.warning(
                f"Доступ запрещён пользователю {user_id} для получения заказов — не покупатель"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ разрешён только покупателям",
            )

        orders = await get_orders_by_buyer(db, user_id)
        logger.info(f"Найдено заказов для пользователя {user_id}: {len(orders)}")

        response = []

        for order in orders:
            # Получаем все цветы и количества в заказе
            result = await db.execute(
                select(ordered_flowers.c.flower_id, ordered_flowers.c.quantity, Flower)
                .join(Flower, Flower.id == ordered_flowers.c.flower_id)
                .where(ordered_flowers.c.order_id == order.id)
            )
            rows = result.fetchall()

            items = []
            seller_id = None

            for flower_id, quantity, flower in rows:
                items.append(
                    {
                        "flower_id": flower_id,
                        "quantity": quantity,
                    }
                )
                # Получаем seller_id по первому цветку (если ещё не получен)
                if seller_id is None:
                    seller_result = await db.execute(
                        select(saleable_flowers.c.seller_id).where(
                            saleable_flowers.c.flower_id == flower_id
                        )
                    )
                    seller_row = seller_result.first()
                    seller_id = seller_row.seller_id if seller_row else None

            response.append(
                OrderResponse(
                    buyer_id=order.buyer_id,
                    order_id=order.id,
                    seller_id=seller_id,
                    order_date=order.order_date,
                    items=items,
                )
            )

        return response
