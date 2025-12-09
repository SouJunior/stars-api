from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property

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

    description = Column(String(300), index=False)

    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="items")


class JobTitle(Base):
    __tablename__ = "jobtitle"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), index=True)
    is_active = Column(Boolean, default=True)

    volunteers = relationship("Volunteer", back_populates="jobtitle")


class VolunteerStatus(Base):
    __tablename__ = "volunteer_status"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, index=True)
    description = Column(String(255))

    volunteers = relationship("Volunteer", back_populates="status")


class Volunteer(Base):
    __tablename__ = "volunteer"

    id = Column(Integer, primary_key=True)
    name = Column(String(45), index=True)
    linkedin = Column(String(255), index=True)
    email = Column(String(255), index=True)
    phone = Column(String(30))
    is_active = Column(Boolean, default=True)
    jobtitle_id = Column(Integer, ForeignKey("jobtitle.id"))
    status_id = Column(Integer, ForeignKey("volunteer_status.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    jobtitle = relationship("JobTitle", back_populates="volunteers")
    status = relationship("VolunteerStatus", back_populates="volunteers")
    status_history = relationship("VolunteerStatusHistory", back_populates="volunteer")

    @hybrid_property
    def masked_email(self):
        if self.email and '@' in self.email:
            parts = self.email.split('@')
            return '***@' + parts[1]
        return self.email # Or return None if preferred for invalid emails


class VolunteerStatusHistory(Base):
    __tablename__ = "volunteer_status_history"

    id = Column(Integer, primary_key=True)
    volunteer_id = Column(Integer, ForeignKey("volunteer.id"))
    status_id = Column(Integer, ForeignKey("volunteer_status.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    volunteer = relationship("Volunteer", back_populates="status_history")
    status = relationship("VolunteerStatus")
