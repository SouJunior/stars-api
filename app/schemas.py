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
    registration_code: str


class User(UserBase):
    id: int
    is_active: bool
    items: list[Item] = []
    volunteer: Optional['Volunteer'] = None

    class Config:
        orm_mode = True

class JobTitle(BaseModel):
    id: int
    title: str
    is_active: bool

    class Config:
        orm_mode = True

class VolunteerInSquad(BaseModel):
    id: int
    name: str
    jobtitle: Optional['JobTitle'] = None
    volunteer_type: Optional['VolunteerType'] = None
    
    class Config:
        orm_mode = True

class ProjectInSquad(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    link: Optional[str] = None

    class Config:
        orm_mode = True

class SquadBase(BaseModel):
    name: str
    description: Optional[str] = None
    discord_role_id: Optional[str] = None

class SquadCreate(SquadBase):
    project_ids: Optional[list[int]] = []

class Squad(SquadBase):
    id: int
    volunteers: list[VolunteerInSquad] = []
    projects: list[ProjectInSquad] = []
    members_count: Optional[int] = 0
    projects_count: Optional[int] = 0
    discord_role_id: Optional[str] = None

    class Config:
        orm_mode = True


class SquadUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    discord_role_id: Optional[str] = None
    project_ids: Optional[list[int]] = None

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

class VolunteerTypeBase(BaseModel):
    name: str
    description: Optional[str] = None

class VolunteerType(VolunteerTypeBase):
    id: int

    class Config:
        orm_mode = True

class VerticalBase(BaseModel):
    name: str
    description: Optional[str] = None

class VerticalCreate(VerticalBase):
    pass

class VerticalUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class VerticalInVolunteer(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        orm_mode = True

class Vertical(VerticalBase):
    id: int

    class Config:
        orm_mode = True

class VerticalWithVolunteers(VerticalBase):
    id: int
    volunteers: list['VolunteerInSquad'] = []

    class Config:
        orm_mode = True

class VolunteerCommon(BaseModel):
    name: str
    linkedin: str
    github: Optional[str] = None
    is_active: Optional[bool]

class VolunteerBase(VolunteerCommon):
    phone: Optional[str] = None
    discord: Optional[str] = None
    email: str

class VolunteerCreate(VolunteerBase):
    # name: str
    # email: str
    # masked_email: Optional[str] = None
    is_active: Optional[bool] = True
    jobtitle_id: int
    volunteer_type_id: Optional[int] = None
    squad_id: Optional[int] = None
    vertical_ids: Optional[list[int]] = None

class FeedbackBase(BaseModel):
    content: str

class FeedbackCreate(FeedbackBase):
    pass

class FeedbackUpdate(FeedbackBase):
    pass

class FeedbackRead(FeedbackBase):
    id: int
    user_id: int
    volunteer_id: int
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    author: Optional[UserBase] = None
    author_name: str
    author_linkedin: Optional[str] = None

    class Config:
        orm_mode = True

class Volunteer(VolunteerBase):
    id: int
    is_apoiase_supporter: Optional[bool] = False
    jobtitle_id: int
    status_id: Optional[int] = None
    volunteer_type_id: Optional[int] = None
    squad_id: Optional[int] = None
    masked_email: Optional[str] = None
    created_at: Optional[datetime] = None
    jobtitle: Optional['JobTitle'] = None
    status: Optional[VolunteerStatus] = None
    volunteer_type: Optional[VolunteerType] = None
    squad: Optional['Squad'] = None
    verticals: list[Vertical] = []
    status_history: list[VolunteerStatusHistory] = []
    feedbacks: list[FeedbackRead] = []

    class Config:
        orm_mode = True

class VolunteerWithEmail(Volunteer):
    pass

class VolunteerPublic(VolunteerCommon):
    id: int
    is_apoiase_supporter: Optional[bool] = False
    discord: Optional[str] = None
    jobtitle_id: int
    status_id: Optional[int] = None
    volunteer_type_id: Optional[int] = None
    squad_id: Optional[int] = None
    masked_email: Optional[str] = None
    created_at: Optional[datetime] = None
    jobtitle: Optional['JobTitle'] = None
    status: Optional[VolunteerStatus] = None
    volunteer_type: Optional[VolunteerType] = None
    squad: Optional['Squad'] = None
    verticals: list[Vertical] = []
    status_history: list[VolunteerStatusHistory] = []
    feedbacks: list[FeedbackRead] = []

    class Config:
        orm_mode = True

class VolunteerList(VolunteerBase):
    id: int
    is_apoiase_supporter: Optional[bool] = False
    jobtitle_id: int
    status_id: Optional[int] = None
    volunteer_type_id: Optional[int] = None
    squad_id: Optional[int] = None
    masked_email: Optional[str] = None
    created_at: Optional[datetime] = None
    jobtitle: Optional['JobTitle'] = None
    status: Optional[VolunteerStatus] = None
    volunteer_type: Optional[VolunteerType] = None
    squad: Optional['Squad'] = None

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


class StatusCount(BaseModel):
    status: str
    count: int


class SquadCount(BaseModel):
    squad: str
    count: int


class VolunteerTypeCount(BaseModel):
    volunteer_type: str
    count: int


class DashboardStats(BaseModel):
    total_volunteers_by_status: list[StatusCount]
    total_volunteers_by_squad: list[SquadCount]
    total_volunteers_by_type: list[VolunteerTypeCount]
    total_volunteers_registered_today: int
    total_volunteers: int


class VolunteerUpdateLinkRequest(BaseModel):
    email: str


class VolunteerUpdateProfile(BaseModel):
    name: str
    linkedin: str
    github: Optional[str] = None
    phone: Optional[str] = None
    discord: Optional[str] = None
    volunteer_type_id: Optional[int] = None
    vertical_ids: Optional[list[int]] = None


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    link: Optional[str] = None


class ProjectCreate(ProjectBase):
    squad_ids: list[int] = []


class Project(ProjectBase):
    id: int
    squads: list[Squad] = []

    class Config:
        orm_mode = True

User.model_rebuild()


class JobOpeningBase(BaseModel):


    title: str


    description: str


    requirements: Optional[str] = None


    is_active: Optional[bool] = True








class JobOpeningCreate(JobOpeningBase):


    pass








class JobOpeningSummary(JobOpeningBase):


    id: int


    created_at: datetime


    owner_id: Optional[int] = None





    class Config:


        orm_mode = True








class JobApplicationBase(BaseModel):


    job_id: int


    volunteer_id: int








class JobApplicationCreate(JobApplicationBase):


    pass








class JobApplication(JobApplicationBase):


    id: int


    created_at: datetime


    job: JobOpeningSummary


    volunteer: Volunteer





    class Config:


        orm_mode = True








class JobOpening(JobOpeningSummary):


    applications: list[JobApplication] = []





    class Config:


        orm_mode = True

