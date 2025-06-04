from datetime import date
from typing import List

from pydantic import BaseModel


class FlowerOrderItem(BaseModel):
    flower_id: int
    quantity: int


class CreateOrder(BaseModel):
    items: List[FlowerOrderItem]


class OrderResponse(BaseModel):
    buyer_id: int
    order_id: int
    order_date: date
    is_closed: bool
    items: List[FlowerOrderItem]


class OrderedFlowerSchema(BaseModel):
    flower_id: int
    quantity: int

    class Config:
        orm_mode = True


class OrderSchema(BaseModel):
    order_id: int
    order_date: date
    buyer_id: int
    is_closed: bool
    items: List[OrderedFlowerSchema]

    class Config:
        orm_mode = True
