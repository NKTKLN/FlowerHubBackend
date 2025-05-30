import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core import auth_service, verify_token
from app.crud import (
    add_flower_to_seller,
    create_flower,
    create_user,
    get_orders,
    get_user_by_id,
    update_user,
)
from app.db import get_session
from app.db.models import Person, User, UserType
from app.schemas import FlowerCreate, FlowerData, OrderSchema, UserData, UserRegister

logger: logging.Logger = logging.getLogger(__name__)


class AdminAPI:
    def __init__(self):
        self.router = APIRouter()
        self.router.post("/users", response_model=UserData)(self.create_user)
        self.router.delete("/users/{user_id}")(self.delete_user)
        self.router.put("/users/{user_id}", response_model=UserData)(self.admin_update_user)
        self.router.get("/users", response_model=list[UserData])(self.list_users)
        self.router.post("/flowers", response_model=FlowerData)(self.add_flower)
        self.router.get("/orders", response_model=List[OrderSchema])(self.admin_get_orders)

    async def _check_admin(self, user_id: int, db: Session):
        person_result = await db.execute(select(Person).filter(Person.user_id == user_id))
        person = person_result.scalars().first()
        if not person:
            raise HTTPException(status_code=403, detail="Пользователь не найден")
        user_type_result = await db.execute(
            select(UserType).filter(UserType.id == person.user_type_id)
        )
        user_type = user_type_result.scalars().first()
        if not user_type or user_type.name != "Админ":
            raise HTTPException(status_code=403, detail="Доступ только для администратора")

    async def create_user(
        self,
        user_data: UserRegister,
        admin_id: int = Depends(verify_token),
        db: Session = Depends(get_session),
    ):
        await self._check_admin(admin_id, db)
        existing_user = await db.execute(select(User).filter(User.email == user_data.email))
        if existing_user.scalars().first():
            raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

        user = await create_user(db, user_data)
        return await get_user_by_id(db, user.id)

    async def delete_user(
        self,
        user_id: int,
        admin_id: int = Depends(verify_token),
        db: Session = Depends(get_session),
    ):
        await self._check_admin(admin_id, db)
        user_result = await db.execute(select(User).filter_by(id=user_id))
        user = user_result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        await db.execute(delete(Person).filter(Person.user_id == user_id))
        await db.execute(delete(User).filter(User.id == user_id))
        await db.commit()
        return {"detail": f"Пользователь с ID {user_id} удалён"}

    async def admin_update_user(
        self,
        user_id: int,
        updated_data: UserData,
        admin_id: int = Depends(verify_token),
        db: Session = Depends(get_session),
    ):
        await self._check_admin(admin_id, db)

        existing_user = await get_user_by_id(db, user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        await update_user(db, user_id, updated_data)
        updated_user = await get_user_by_id(db, user_id)
        return updated_user

    async def list_users(
        self,
        admin_id: int = Depends(verify_token),
        db: Session = Depends(get_session),
    ):
        await self._check_admin(admin_id, db)
        query = (
            select(User, Person, UserType)
            .join(Person, Person.user_id == User.id)
            .join(UserType, UserType.id == Person.user_type_id)
        )
        result = await db.execute(query)
        users = []
        for user, person, user_type in result.all():
            users.append(
                UserData(
                    id=user.id,
                    email=user.email,
                    first_name=person.first_name,
                    last_name=person.last_name,
                    display_name=person.display_name,
                    is_user_seller=user_type.name == "Продавец",
                    is_user_admin=user_type.name == "Админ",
                    address=None,
                )
            )
        return users

    async def add_flower(
        self,
        flower_data: FlowerCreate,
        seller_id: int,
        admin_id: int = Depends(verify_token),
        db: AsyncSession = Depends(get_session),
    ):
        logger.info(f"Пользователь {admin_id} пытается добавить цветок")
        await self._check_admin(admin_id, db)
        flower = await create_flower(db, flower_data)
        await add_flower_to_seller(db, flower.id, seller_id)
        logger.info(f"Цветок добавлен пользователем {admin_id}, ID цветка: {flower.id}")
        return flower

    async def admin_get_orders(
        self,
        admin_id: int = Depends(verify_token),
        db: AsyncSession = Depends(get_session),
    ):
        logger.info(f"Пользователь {admin_id} запрашивает заказы")
        await self._check_admin(admin_id, db)

        orders = await get_orders(db)
        logger.info(f"Пользователь {admin_id} получил {len(orders)} заказов")
        return orders
