from pydantic import BaseModel
from typing import Optional, Union
from datetime import datetime


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

class VolunteerStatusBase(BaseModel):
    name: str
    description: Optional[str] = None

class VolunteerStatusCreate(VolunteerStatusBase):
    pass

class VolunteerStatus(VolunteerStatusBase):
    id: int

    class Config:
        orm_mode = True

class VolunteerStatusHistoryBase(BaseModel):
    status_id: int
    created_at: datetime

class VolunteerStatusHistory(VolunteerStatusHistoryBase):
    id: int
    status: VolunteerStatus

    class Config:
        orm_mode = True

class VolunteerBase(BaseModel):
    name: str
    linkedin: str
    # email: str
    is_active: Optional[bool]

class VolunteerCreate(VolunteerBase):
    # name: str
    email: str
    # masked_email: Optional[str] = None
    is_active: Optional[bool] = True
    jobtitle_id: int

class Volunteer(VolunteerBase):
    id: int
    jobtitle_id: int
    status_id: Optional[int] = None
    masked_email: Optional[str] = None
    created_at: Optional[datetime] = None
    jobtitle: Optional['JobTitle'] = None
    status: Optional[VolunteerStatus] = None
    status_history: list[VolunteerStatusHistory] = []

    class Config:
        orm_mode = True

class VolunteerList(VolunteerBase):
    id: int
    jobtitle_id: int
    status_id: Optional[int] = None
    masked_email: Optional[str] = None
    created_at: Optional[datetime] = None
    jobtitle: Optional['JobTitle'] = None
    status: Optional[VolunteerStatus] = None

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Union[str, None] = None


class UserAuth(BaseModel):
    username: str
    email: str
    is_active: Union[bool, None] = None

class UserInDB(UserAuth):
    hashed_password: str

