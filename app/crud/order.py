import logging
from datetime import date

from fastapi import HTTPException
from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.db.models import Flower, Order, Person, ordered_flowers, saleable_flowers
from app.schemas import OrderedFlowerSchema, OrderSchema

logger = logging.getLogger(__name__)


async def create_order_by_buyer(session: AsyncSession, buyer_id: int, items: list[dict]):
    logger.info(f"Создание заказа для покупателя с ID {buyer_id} с товарами: {items}")

    result = await session.execute(select(Person).filter_by(user_id=buyer_id))
    buyer = result.scalars().first()
    if not buyer:
        logger.warning(f"Покупатель с ID {buyer_id} не найден")
        raise HTTPException(status_code=404, detail="Покупатель не найден")

    # Группировка товаров по продавцу
    flowers = []
    for item in items:
        flower_result = await session.execute(select(Flower).filter_by(id=item["flower_id"]))
        flower = flower_result.scalars().first()
        if not flower:
            logger.warning(f"Цветок с ID {item['flower_id']} не найден")
            raise HTTPException(
                status_code=404, detail=f"Цветок с ID {item['flower_id']} не найден"
            )

        flowers.append((flower, item["quantity"]))

    created_orders = []
    order = Order(buyer_id=buyer.id, order_date=date.today())
    session.add(order)
    await session.flush()
    logger.info(f"Создан заказ с ID {order.id}")

    for flower, quantity in flowers:
        await session.execute(
            ordered_flowers.insert().values(
                order_id=order.id, flower_id=flower.id, quantity=quantity
            )
        )
        logger.info(f"Добавлен цветок ID {flower.id} (кол-во {quantity}) в заказ ID {order.id}")

        created_orders.append(order)

    await session.commit()
    return created_orders


async def get_orders_by_buyer(db: AsyncSession, buyer_id: int):
    result = await db.execute(select(Order).where(Order.buyer_id == buyer_id))
    return result.scalars().all()


async def get_orders_by_seller(db: AsyncSession, seller_id: int):
    logger.info(f"Получение заказов, связанных с продавцом {seller_id}")

    # Найдём все заказы, в которых есть цветы, продаваемые данным продавцом
    stmt = (
        select(Order)
        .distinct()
        .join(ordered_flowers, Order.id == ordered_flowers.c.order_id)
        .join(Flower, Flower.id == ordered_flowers.c.flower_id)
        .join(saleable_flowers, Flower.id == saleable_flowers.c.flower_id)
        .filter(saleable_flowers.c.seller_id == seller_id)
    )

    result = await db.execute(stmt)
    orders = result.unique().scalars().all()
    logger.info(f"Найдено заказов: {len(orders)}")
    order_schemas = []

    for order in orders:
        stmt_items = select(ordered_flowers).where(ordered_flowers.c.order_id == order.id)
        result_items = await db.execute(stmt_items)
        ordered_items = result_items.all()

        # Построим список OrderedFlowerSchema
        items = [
            OrderedFlowerSchema(flower_id=item.flower_id, quantity=item.quantity)
            for item in ordered_items
        ]

        order_schemas.append(
            OrderSchema(
                order_date=order.order_date, buyer_id=order.buyer_id, order_id=order.id, items=items
            )
        )
    return order_schemas


async def get_orders(db: AsyncSession):
    # Найдём все заказы, в которых есть цветы, продаваемые данным продавцом
    stmt = (
        select(Order)
        .distinct()
        .join(ordered_flowers, Order.id == ordered_flowers.c.order_id)
        .join(Flower, Flower.id == ordered_flowers.c.flower_id)
        .join(saleable_flowers, Flower.id == saleable_flowers.c.flower_id)
    )

    result = await db.execute(stmt)
    orders = result.unique().scalars().all()
    logger.info(f"Найдено заказов: {len(orders)}")
    order_schemas = []

    for order in orders:
        stmt_items = select(ordered_flowers).where(ordered_flowers.c.order_id == order.id)
        result_items = await db.execute(stmt_items)
        ordered_items = result_items.all()

        # Построим список OrderedFlowerSchema
        items = [
            OrderedFlowerSchema(flower_id=item.flower_id, quantity=item.quantity)
            for item in ordered_items
        ]

        order_schemas.append(
            OrderSchema(
                order_date=order.order_date, buyer_id=order.buyer_id, order_id=order.id, items=items
            )
        )
    return order_schemas


async def get_order_by_id(db: AsyncSession, order_id: int) -> Order | None:
    result = await db.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()
