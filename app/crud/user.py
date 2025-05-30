import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import auth_service
from app.db.models import Address, Country, Person, User, UserRole, UserType
from app.schemas import UserAddress, UserData, UserRegister

default_types = ["Покупатель", "Продавец", "Админ"]

logger: logging.Logger = logging.getLogger(__name__)


async def create_default_user_types(session: Session):
    for type_name in default_types:
        result = await session.execute(select(UserType).filter_by(name=type_name))
        exists = result.scalars().first()
        if not exists:
            logger.info(f"Создание типа пользователя: {type_name}")
            session.add(UserType(name=type_name))
    await session.commit()
    logger.info("Типы пользователей успешно созданы или уже существуют.")


async def get_user_type_id(db: Session, name: str) -> int:
    if name not in default_types:
        logger.error(f"Неверный тип пользователя: {name}")
        raise ValueError(f"Invalid user type name: {name}. Must be one of {default_types}")

    result = await db.execute(select(UserType).filter_by(name=name))
    user_type = result.scalars().first()

    if user_type:
        return user_type.id

    logger.info(f"Тип пользователя '{name}' не найден. Создание нового.")
    user_type = UserType(name=name)
    db.add(user_type)
    await db.commit()
    await db.refresh(user_type)
    return user_type.id


async def get_user_by_email(db: Session, email: str):
    logger.info(f"Поиск пользователя по email: {email}")
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()


async def get_user_by_id(db: Session, user_id: int):
    logger.info(f"Получение пользователя по ID: {user_id}")
    user_result = await db.execute(select(User).filter(User.id == user_id))
    user_data: User = user_result.scalars().first()
    if user_data is None:
        logger.warning(f"Пользователь с ID {user_id} не найден.")
        return None

    person_result = await db.execute(select(Person).filter(Person.user_id == user_id))
    person_data: Person = person_result.scalars().first()
    if person_data is None:
        logger.warning(f"Персона пользователя с ID {user_id} не найдена.")
        return None

    user_type_result = await db.execute(
        select(UserType).filter(UserType.id == person_data.user_type_id)
    )
    user_type: UserType = user_type_result.scalars().first()
    if user_type is None:
        logger.warning(f"Тип пользователя с ID {user_id} не найден.")
        return None
    is_user_seller = user_type.name == "Продавец"
    is_user_admin = user_type.name == "Админ"

    user_address = None
    if person_data.address_id:
        user_address_result = await db.execute(
            select(Address).filter(Address.id == person_data.address_id)
        )
        address: Optional[Address] = user_address_result.scalars().first()
        if address:
            country_result = await db.execute(
                select(Country).filter(Country.id == address.country_id)
            )
            country: Country = country_result.scalars().first()
            if country:
                user_address = UserAddress(
                    street=address.street,
                    city=address.city,
                    postal_code=address.postal_code,
                    country_name=country.name,
                    country_code=country.code,
                )
            else:
                logger.warning("Страна не найдена для адреса пользователя.")

    return UserData(
        id=user_data.id,
        email=user_data.email,
        first_name=person_data.first_name,
        last_name=person_data.last_name,
        display_name=person_data.display_name,
        is_user_seller=is_user_seller,
        is_user_admin=is_user_admin,
        address=user_address,
    )


async def update_user(db: Session, user_id: int, new_data: UserData) -> None:
    logger.info(f"Обновление данных пользователя ID: {user_id}")
    required_fields = [
        new_data.email,
        new_data.first_name,
        new_data.last_name,
        new_data.display_name,
    ]
    if any(field is None or field.strip() == "" for field in required_fields):
        logger.error("Обязательные поля не заполнены.")
        raise HTTPException(status_code=400, detail="Обязательные поля не могут быть пустыми")

    if new_data.address:
        address_fields = [
            new_data.address.street,
            new_data.address.city,
            new_data.address.postal_code,
            new_data.address.country_name,
            new_data.address.country_code,
        ]
        if any(field is None or field.strip() == "" for field in address_fields):
            logger.error("Некорректные данные адреса.")
            raise HTTPException(
                status_code=400,
                detail="Все поля адреса обязательны, если адрес передан",
            )

    user_result = await db.execute(select(User).filter_by(id=user_id))
    user = user_result.scalars().first()
    if not user:
        logger.error(f"Пользователь с ID {user_id} не найден.")
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    person_result = await db.execute(select(Person).filter_by(user_id=user_id))
    person = person_result.scalars().first()
    if not person:
        logger.error(f"Персона пользователя с ID {user_id} не найдена.")
        raise HTTPException(status_code=404, detail="Персона пользователя не найдена")

    user.email = new_data.email
    person.first_name = new_data.first_name
    person.last_name = new_data.last_name
    person.display_name = new_data.display_name

    user_type_name = "Продавец" if new_data.is_user_seller else "Покупатель"
    person.user_type_id = await get_user_type_id(db, user_type_name)

    if new_data.address:
        country_result = await db.execute(
            select(Country).filter_by(code=new_data.address.country_code)
        )
        country = country_result.scalars().first()
        if not country:
            logger.info(f"Создание новой страны: {new_data.address.country_name}")
            country = Country(
                name=new_data.address.country_name, code=new_data.address.country_code
            )
            db.add(country)
            await db.flush()

        if person.address_id:
            address_result = await db.execute(select(Address).filter_by(id=person.address_id))
            address = address_result.scalars().first()
            if address:
                address.street = new_data.address.street
                address.city = new_data.address.city
                address.postal_code = new_data.address.postal_code
                address.country_id = country.id
            else:
                logger.error("Адрес не найден.")
                raise HTTPException(status_code=404, detail="Адрес не найден")
        else:
            address = Address(
                street=new_data.address.street,
                city=new_data.address.city,
                postal_code=new_data.address.postal_code,
                country_id=country.id,
            )
            db.add(address)
            await db.flush()
            person.address_id = address.id

    await db.commit()
    logger.info(f"Пользователь с ID {user_id} успешно обновлен.")


async def update_password(db: Session, user_id: int, new_password: str) -> None:
    if not new_password or len(new_password) < 8:
        logger.warning("Попытка установить короткий пароль.")
        raise HTTPException(status_code=400, detail="Пароль должен содержать минимум 8 символов")

    result = await db.execute(select(User).filter_by(id=user_id))
    user = result.scalars().first()
    if not user:
        logger.error(f"Пользователь с ID {user_id} не найден.")
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    user.password_hash = auth_service.get_password_hash(new_password)
    await db.commit()
    logger.info(f"Пароль пользователя ID {user_id} успешно обновлен.")


async def create_user(db: Session, user_data: UserRegister) -> User:
    logger.info(f"Создание нового пользователя: {user_data.email}")
    type_name = "Продавец" if user_data.is_user_seller else "Покупатель"
    user_type_id = await get_user_type_id(db, type_name)
    hashed_password = auth_service.get_password_hash(user_data.password)

    user = User(email=user_data.email, password_hash=hashed_password)
    db.add(user)
    await db.flush()

    db_person = Person(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        display_name=f"{user_data.first_name} {user_data.last_name}",
        user_id=user.id,
        user_type_id=user_type_id,
    )
    db.add(db_person)
    await db.commit()
    await db.refresh(db_person)

    logger.info(f"Пользователь создан с ID {user.id}")
    return user


async def create_admin(db: Session, user_data: UserRegister) -> User:
    logger.info(f"Создание нового пользователя: {user_data.email}")
    type_name = "Админ"
    user_type_id = await get_user_type_id(db, type_name)
    hashed_password = auth_service.get_password_hash(user_data.password)

    user = User(email=user_data.email, password_hash=hashed_password)
    db.add(user)
    await db.flush()

    db_person = Person(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        display_name=f"{user_data.first_name} {user_data.last_name}",
        user_id=user.id,
        user_type_id=user_type_id,
    )
    db.add(db_person)
    await db.commit()
    await db.refresh(db_person)

    logger.info(f"Пользователь создан с ID {user.id}")
    return user
