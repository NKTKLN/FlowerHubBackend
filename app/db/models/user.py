from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.db.models.flower import saleable_flowers


class UserRole(Base):
    __tablename__ = "user_role"

    id = Column(Integer, primary_key=True)
    name = Column(String)


class UserType(Base):
    __tablename__ = "user_type"

    id = Column(Integer, primary_key=True)
    name = Column(String)


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("user_role.id"), nullable=False)

    role = relationship("UserRole")


class Person(Base):
    __tablename__ = "person"

    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    display_name = Column(String(150))
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("address.id"))
    user_type_id = Column(Integer, ForeignKey("user_type.id"), nullable=False)

    user = relationship("User")
    address = relationship("Address")
    user_type = relationship("UserType")
    flowers_for_sale = relationship("Flower", secondary=saleable_flowers, back_populates="sellers")
    orders = relationship("Order", back_populates="buyer")
