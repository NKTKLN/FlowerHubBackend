from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class Address(Base):
    __tablename__ = "address"

    id = Column(Integer, primary_key=True)
    street = Column(String)
    city = Column(String)
    postal_code = Column(String)
    country_id = Column(Integer, ForeignKey("country.id"))

    country = relationship("Country")


class Country(Base):
    __tablename__ = "country"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    code = Column(String)
