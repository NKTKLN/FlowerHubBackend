from sqlalchemy import Column, Date, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.db.models.flower import ordered_flowers


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    buyer_id = Column(Integer, ForeignKey("person.id"))
    order_date = Column(Date)

    buyer = relationship("Person", back_populates="orders")
    flowers = relationship("Flower", secondary=ordered_flowers, back_populates="orders")
