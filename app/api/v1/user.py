import logging

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core import auth_service, verify_token
from app.crud import get_user_by_id, update_password, update_user
from app.db import get_session
from app.schemas import UserData

logger: logging.Logger = logging.getLogger(__name__)


class UserAPI:
    def __init__(self):
        self.router = APIRouter()

        # Регистрация маршрутов
        self.router.get("/", response_model=UserData)(self.get_user)
        self.router.get("/{user_id}", response_model=UserData)(self.get_user_by_id)
        self.router.put("/")(self.update_user_data)
        self.router.put("/password")(self.update_user_password)

    async def get_user_by_id(
        self,
        user_id: int,
        token: str = Header(None, alias="X-Token"),
        db: Session = Depends(get_session),
    ):
        get_user_data = None
        if token is not None:
            payload = auth_service.decode_token(token)
            if payload is not None:
                get_user_id: str = payload.get("sub")
                if get_user_id is not None:
                    get_user_data = await get_user_by_id(db, get_user_id)

        logger.info(f"Запрос данных пользователя с ID: {user_id}")
        user_data = await get_user_by_id(db, user_id)
        if user_data is None:
            logger.warning(f"Пользователь с ID {user_id} не найден или данные некорректны")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Данные пользователя недействительны",
            )
        logger.info(f"Данные пользователя с ID {user_id} успешно получены")
        if (
            (
                get_user_data is None
                or not (get_user_data.is_user_seller or get_user_data.is_user_admin)
            )
            and get_user_data.id != user_id
            and not user_data.is_user_seller
        ):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Отказано в доступе",
            )

        return user_data

    async def get_user(
        self, user_id: str = Depends(verify_token), db: Session = Depends(get_session)
    ):
        logger.info(f"Запрос данных пользователя с ID: {user_id}")
        user_data = await get_user_by_id(db, user_id)
        if user_data is None:
            logger.warning(f"Пользователь с ID {user_id} не найден или данные некорректны")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Данные пользователя недействительны",
            )
        logger.info(f"Данные пользователя с ID {user_id} успешно получены")
        return user_data

    async def update_user_data(
        self,
        user_data: UserData,
        user_id: str = Depends(verify_token),
        db: Session = Depends(get_session),
    ):
        logger.info(f"Пользователь с ID {user_id} пытается обновить свои данные")
        await update_user(db, user_id, user_data)
        logger.info(f"Данные пользователя с ID {user_id} успешно обновлены")
        return {"detail": "Данные пользователя успешно обновлены"}

    async def update_user_password(
        self,
        new_password: str,
        user_id: str = Depends(verify_token),
        db: Session = Depends(get_session),
    ):
        logger.info(f"Пользователь с ID {user_id} пытается изменить пароль")
        await update_password(db, user_id, new_password)
        logger.info(f"Пароль пользователя с ID {user_id} успешно обновлен")
        return {"detail": "Данные пользователя успешно обновлены"}
