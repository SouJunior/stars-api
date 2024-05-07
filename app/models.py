from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(320), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)

    items = relationship("Item", back_populates="owner")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), index=True)
    description = Column(Text(3000), index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="items")


class JobTitle(Base):
    __tablename__ = "jobtitle"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), index=True)
    is_active = Column(Boolean, default=True)

    volunteers = relationship("Volunteer", back_populates="jobtitle")


class Volunteer(Base):
    __tablename__ = "volunteer"

    id = Column(Integer, primary_key=True)
    name = Column(String(45), index=True)
    linkedin = Column(String(3072), index=True)
    email = Column(String(320), index=True)
    is_active = Column(Boolean, default=True)
    jobtitle_id = Column(Integer, ForeignKey("jobtitle.id"))

    jobtitle = relationship("JobTitle", back_populates="volunteers")
