from typing import Optional

from pydantic import BaseModel

from app.schemas.address import UserAddress


class UserLogin(BaseModel):
    email: str
    password: str


class UserRegister(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    is_user_seller: bool = False


class UserData(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    display_name: str
    is_user_seller: bool
    is_user_admin: bool
    address: Optional[UserAddress]
