import enum
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, Date, Table, Enum
from sqlalchemy.orm import relationship, foreign, remote
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property

from .database import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    HEAD = "HEAD"
    MENTOR = "MENTOR"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(320), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.MENTOR, nullable=False)
    reset_token = Column(String(255), nullable=True, index=True)
    reset_token_expires_at = Column(DateTime, nullable=True)

    items = relationship("Item", back_populates="owner")
    feedbacks = relationship("Feedback", back_populates="author")
    certificates_issued = relationship("Certificate", back_populates="issuer")
    badges_issued = relationship("Badge", back_populates="issuer")
    volunteer = relationship(
        "Volunteer",
        primaryjoin="foreign(User.email) == remote(Volunteer.email)",
        uselist=False,
        viewonly=True,
    )


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


project_squad_association = Table(
    'project_squad', Base.metadata,
    Column('project_id', Integer, ForeignKey('project.id'), primary_key=True),
    Column('squad_id', Integer, ForeignKey('squad.id'), primary_key=True)
)


class Squad(Base):
    __tablename__ = "squad"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, index=True)
    description = Column(String(255), nullable=True)
    discord_role_id = Column(String(255), nullable=True)

    volunteers = relationship("Volunteer", back_populates="squad")
    projects = relationship("Project", secondary=project_squad_association, back_populates="squads")


volunteer_vertical_association = Table(
    'volunteer_vertical', Base.metadata,
    Column('volunteer_id', Integer, ForeignKey('volunteer.id'), primary_key=True),
    Column('vertical_id', Integer, ForeignKey('vertical.id'), primary_key=True)
)


mentor_mentee_association = Table(
    'mentor_mentee', Base.metadata,
    Column('mentor_id', Integer, ForeignKey('volunteer.id'), primary_key=True),
    Column('mentee_id', Integer, ForeignKey('volunteer.id'), primary_key=True)
)


class Vertical(Base):
    __tablename__ = "vertical"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, index=True)
    description = Column(String(255), nullable=True)

    volunteers = relationship("Volunteer", secondary=volunteer_vertical_association, back_populates="verticals")


class Project(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), index=True)
    description = Column(Text)
    link = Column(String(255))

    squads = relationship("Squad", secondary=project_squad_association, back_populates="projects")


class VolunteerStatus(Base):
    __tablename__ = "volunteer_status"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, index=True)
    description = Column(String(255))

    volunteers = relationship("Volunteer", back_populates="status")


class VolunteerType(Base):
    __tablename__ = "volunteer_type"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, index=True)
    description = Column(String(255))
    order = Column(Integer, default=999)

    volunteers = relationship("Volunteer", back_populates="volunteer_type")


class Volunteer(Base):
    __tablename__ = "volunteer"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), index=True)
    linkedin = Column(String(255), index=True)
    github = Column(String(255), index=True, nullable=True)
    email = Column(String(255), index=True)
    phone = Column(String(30))
    discord = Column(String(255), nullable=True)
    discord_invite_sent = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_apoiase_supporter = Column(Boolean, default=False)
    jobtitle_id = Column(Integer, ForeignKey("jobtitle.id"))
    status_id = Column(Integer, ForeignKey("volunteer_status.id"), nullable=True)
    volunteer_type_id = Column(Integer, ForeignKey("volunteer_type.id"), nullable=True)
    squad_id = Column(Integer, ForeignKey("squad.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    jobtitle = relationship("JobTitle", back_populates="volunteers")
    status = relationship("VolunteerStatus", back_populates="volunteers")
    volunteer_type = relationship("VolunteerType", back_populates="volunteers")
    squad = relationship("Squad", back_populates="volunteers")
    status_history = relationship("VolunteerStatusHistory", back_populates="volunteer")
    feedbacks = relationship("Feedback", back_populates="volunteer")
    badges = relationship("Badge", back_populates="volunteer")
    verticals = relationship("Vertical", secondary=volunteer_vertical_association, back_populates="volunteers")
    certificates = relationship("Certificate", back_populates="volunteer")
    mentees = relationship(
        "Volunteer",
        secondary=mentor_mentee_association,
        primaryjoin=(id == mentor_mentee_association.c.mentor_id),
        secondaryjoin=(id == mentor_mentee_association.c.mentee_id),
        back_populates="mentors",
    )
    mentors = relationship(
        "Volunteer",
        secondary=mentor_mentee_association,
        primaryjoin=(id == mentor_mentee_association.c.mentee_id),
        secondaryjoin=(id == mentor_mentee_association.c.mentor_id),
        back_populates="mentees",
    )

    edit_token = Column(String(255), nullable=True, index=True)
    edit_token_expires_at = Column(DateTime, nullable=True)
    daily_edits_count = Column(Integer, default=0)
    last_edit_date = Column(Date, nullable=True)

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


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    volunteer_id = Column(Integer, ForeignKey("volunteer.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    author = relationship("User", back_populates="feedbacks")
    volunteer = relationship("Volunteer", back_populates="feedbacks")

    @property
    def author_name(self):
        if self.author and self.author.volunteer:
            return self.author.volunteer.name
        return "***"

    @property
    def author_linkedin(self):
        if self.author and self.author.volunteer:
            return self.author.volunteer.linkedin
        return None


class JobOpening(Base):
    __tablename__ = "job_opening"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), index=True, nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User")
    applications = relationship("JobApplication", back_populates="job")


class JobApplication(Base):
    __tablename__ = "job_application"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("job_opening.id"))
    volunteer_id = Column(Integer, ForeignKey("volunteer.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("JobOpening", back_populates="applications")
    volunteer = relationship("Volunteer")


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True)
    volunteer_id = Column(Integer, ForeignKey("volunteer.id"), nullable=False)
    hours = Column(Integer, nullable=False)
    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    is_cancelled = Column(Boolean, default=False)
    certificate_type = Column(String(50), default="participation")
    issuer_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    volunteer = relationship("Volunteer", back_populates="certificates")
    issuer = relationship("User", back_populates="certificates_issued")


class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    volunteer_id = Column(Integer, ForeignKey("volunteer.id"), nullable=False)
    issuer_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    volunteer = relationship("Volunteer", back_populates="badges")
    issuer = relationship("User", back_populates="badges_issued")

    @property
    def issuer_name(self):
        if self.issuer and self.issuer.volunteer:
            return self.issuer.volunteer.name
        return "***"
