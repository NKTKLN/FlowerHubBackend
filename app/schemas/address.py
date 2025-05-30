from pydantic import BaseModel


class UserAddress(BaseModel):
    street: str
    city: str
    postal_code: str
    country_name: str
    country_code: str
