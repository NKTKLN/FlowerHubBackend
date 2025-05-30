from typing import List, Optional

from pydantic import BaseModel


class FlowerFilter(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    type_id: Optional[int] = None
    season_id: Optional[int] = None
    usage_id: Optional[int] = None
    country_id: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    seller_id: Optional[int] = None


class Pagination(BaseModel):
    limit: int = 100
    offset: int = 0


class FlowerData(BaseModel):
    id: int
    name: str
    type_id: int
    season_id: int
    usage_id: int
    variety: Optional[str]
    price: float
    country_id: int
    seller_ids: List[int] = []

    class Config:
        orm_mode = True


class FlowerCreate(BaseModel):
    name: str
    type_id: int
    season_id: int
    usage_id: int
    country_id: int
    variety: str
    price: float


class FlowerTypeCreate(BaseModel):
    name: str
    description: str


class FloweringSeasonCreate(BaseModel):
    name: str
    description: str


class FlowerUsageCreate(BaseModel):
    name: str
    description: str


class FlowerCountryCreate(BaseModel):
    name: str
    code: str


class FlowerUpdate(BaseModel):
    name: Optional[str] = None
    type_id: Optional[int] = None
    season_id: Optional[int] = None
    usage_id: Optional[int] = None
    country_id: Optional[int] = None
    price: Optional[float] = None
    variety: Optional[str] = None


class FlowerTypeData(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        orm_mode = True


class FloweringSeasonData(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        orm_mode = True


class FlowerUsageData(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        orm_mode = True


class FloweringcountriesData(BaseModel):
    id: int
    name: str
    code: str

    class Config:
        orm_mode = True
