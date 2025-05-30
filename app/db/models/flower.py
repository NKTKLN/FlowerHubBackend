from sqlalchemy import DECIMAL, Column, ForeignKey, Integer, String, Table, CheckConstraint
from sqlalchemy.orm import relationship

from app.db.database import Base

# Ассоциативные таблицы
saleable_flowers = Table(
    "saleable_flowers",
    Base.metadata,
    Column("seller_id", Integer, ForeignKey("person.id"), primary_key=True),
    Column("flower_id", Integer, ForeignKey("flower.id"), primary_key=True),
)

ordered_flowers = Table(
    "ordered_flowers",
    Base.metadata,
    Column("order_id", Integer, ForeignKey("orders.id"), primary_key=True),
    Column("flower_id", Integer, ForeignKey("flower.id"), primary_key=True),
    Column("quantity", Integer, nullable=False),
)


class FlowerType(Base):
    __tablename__ = "flower_type"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)


class FloweringSeason(Base):
    __tablename__ = "flowering_season"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)


class FlowerUsage(Base):
    __tablename__ = "flower_usage"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)


class Flower(Base):
    __tablename__ = "flower"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    type_id = Column(Integer, ForeignKey("flower_type.id"), nullable=False)
    season_id = Column(Integer, ForeignKey("flowering_season.id"))
    usage_id = Column(Integer, ForeignKey("flower_usage.id"))
    variety = Column(String(100))
    price = Column(DECIMAL(10, 2), nullable=False)
    country_id = Column(Integer, ForeignKey("country.id"))

    __table_args__ = (
        CheckConstraint(price > 0, name='check_price_positive'),
    )

    flower_type = relationship("FlowerType")
    season = relationship("FloweringSeason")
    usage = relationship("FlowerUsage")
    country = relationship("Country")
    sellers = relationship("Person", secondary=saleable_flowers, back_populates="flowers_for_sale")
    orders = relationship("Order", secondary=ordered_flowers, back_populates="flowers")

