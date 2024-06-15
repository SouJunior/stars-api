from pydantic import BaseModel
from typing import Optional, Union


class ItemBase(BaseModel):
    title: str
    description: str | None = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    items: list[Item] = []

    class Config:
        orm_mode = True

class JobTitle(BaseModel):
    id: int
    title: str
    is_active: bool

    class Config:
        orm_mode = True

class VolunteerBase(BaseModel):
    name: str
    linkedin: str
    # email: str
    is_active: bool

class VolunteerCreate(VolunteerBase):
    name: str
    email: str
    masked_email: Optional[str] = None
    is_active: Optional[bool] = True # type:ignore
    jobtitle_id: int

class Volunteer(VolunteerBase):
    id: int
    jobtitle_id: int
    masked_email: Optional[str] = None


    class Config:
        orm_mode = True

