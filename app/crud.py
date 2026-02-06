from sqlalchemy.orm import Session, joinedload
from sqlalchemy import create_engine, Column, Integer, String, Boolean, func
from . import models, schemas
from app.auth import get_password_hash
from app.utils import generate_edit_token
from datetime import datetime, timedelta, timezone, date

try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Fallback for systems without zoneinfo data
    class ZoneInfo:
        def __init__(self, key):
             self.key = key
        def utcoffset(self, dt):
             if self.key == "America/Sao_Paulo":
                 return timedelta(hours=-3)
             return timedelta(0)
        def dst(self, dt):
             return timedelta(0)
        def tzname(self, dt):
             return self.key


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()


def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_volunteers(db: Session, skip: int = 0, limit: int = 100, name: str = None, email: str = None, jobtitle_id: int = None, status_id: int = None, volunteer_type_id: int = None, squad_id: int = None, order: str = "desc"):
    query = db.query(models.Volunteer).options(
        joinedload(models.Volunteer.jobtitle),
        joinedload(models.Volunteer.status),
        joinedload(models.Volunteer.volunteer_type),
        joinedload(models.Volunteer.squad),
        joinedload(models.Volunteer.status_history).joinedload(models.VolunteerStatusHistory.status)
    )
    if name:
        query = query.filter(models.Volunteer.name.ilike(f"%{name}%"))
    if email:
        query = query.filter(models.Volunteer.email.ilike(f"%{email}%"))
    if jobtitle_id:
        query = query.filter(models.Volunteer.jobtitle_id == jobtitle_id)
    if status_id:
        query = query.filter(models.Volunteer.status_id == status_id)
    if volunteer_type_id:
        query = query.filter(models.Volunteer.volunteer_type_id == volunteer_type_id)
    if squad_id:
        query = query.filter(models.Volunteer.squad_id == squad_id)

    if order == "desc":
        query = query.order_by(models.Volunteer.created_at.desc())
    else:
        query = query.order_by(models.Volunteer.created_at.asc())

    return query.offset(skip).limit(limit).all()

def get_volunteer_by_id(db: Session, volunteer_id: int):
    return db.query(models.Volunteer).options(
        joinedload(models.Volunteer.jobtitle),
        joinedload(models.Volunteer.status),
        joinedload(models.Volunteer.volunteer_type),
        joinedload(models.Volunteer.squad),
        joinedload(models.Volunteer.status_history).joinedload(models.VolunteerStatusHistory.status),
        joinedload(models.Volunteer.feedbacks).joinedload(models.Feedback.author).joinedload(models.User.volunteer)
    ).filter(models.Volunteer.id == volunteer_id).first()

def get_volunteer_by_email(db: Session, email: str):
    return db.query(models.Volunteer)\
        .options(
            joinedload(models.Volunteer.jobtitle),
            joinedload(models.Volunteer.status),
            joinedload(models.Volunteer.volunteer_type),
            joinedload(models.Volunteer.squad),
            joinedload(models.Volunteer.status_history).joinedload(models.VolunteerStatusHistory.status)
        )\
        .filter(models.Volunteer.email == email).first()

def create_volunteer(db: Session, volunteer: schemas.VolunteerCreate, jobtitle_id: int):
    # Get default status "INTERESTED"
    default_status = db.query(models.VolunteerStatus).filter(models.VolunteerStatus.name == "INTERESTED").first()
    if not default_status:
        raise ValueError("Default status 'INTERESTED' not found.")
    
    # Get default volunteer type "Junior" if not provided
    if not volunteer.volunteer_type_id:
        default_type = db.query(models.VolunteerType).filter(models.VolunteerType.name == "Junior").first()
        if default_type:
            volunteer.volunteer_type_id = default_type.id

    db_volunteer = models.Volunteer(**volunteer.dict(exclude_unset=True))
    # Ensure jobtitle_id is set if it wasn't in the dict (though schema says it is required)
    if not db_volunteer.jobtitle_id:
         db_volunteer.jobtitle_id = jobtitle_id

    if not db_volunteer.status_id:
        db_volunteer.status_id = default_status.id

    db.add(db_volunteer)
    db.commit()
    db.refresh(db_volunteer)

    # Add initial status to history
    status_history_entry = models.VolunteerStatusHistory(
        volunteer_id=db_volunteer.id,
        status_id=db_volunteer.status_id
    )
    db.add(status_history_entry)
    db.commit()
    db.refresh(db_volunteer)
    return db_volunteer

def get_jobtitles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.JobTitle).offset(skip).limit(limit).all()


# Squad CRUD
def get_squads(db: Session, skip: int = 0, limit: int = 100):
    squads = db.query(models.Squad).options(
        joinedload(models.Squad.volunteers).joinedload(models.Volunteer.jobtitle),
        joinedload(models.Squad.volunteers).joinedload(models.Volunteer.volunteer_type)
    ).offset(skip).limit(limit).all()
    
    for squad in squads:
        squad.members_count = len(squad.volunteers)
        
    return squads

def get_squad(db: Session, squad_id: int):
    squad = db.query(models.Squad).options(
        joinedload(models.Squad.volunteers).joinedload(models.Volunteer.jobtitle),
        joinedload(models.Squad.volunteers).joinedload(models.Volunteer.volunteer_type)
    ).filter(models.Squad.id == squad_id).first()
    
    if squad:
        squad.members_count = len(squad.volunteers)
        
    return squad

def create_squad(db: Session, squad: schemas.SquadCreate):
    db_squad = models.Squad(name=squad.name, description=squad.description, discord_role_id=squad.discord_role_id)
    db.add(db_squad)
    db.commit()
    db.refresh(db_squad)
    return db_squad

def update_squad(db: Session, squad_id: int, squad: schemas.SquadUpdate):
    db_squad = db.query(models.Squad).filter(models.Squad.id == squad_id).first()
    if not db_squad:
        return None

    for var, value in vars(squad).items():
        if value is not None:
            setattr(db_squad, var, value)

    db.commit()
    db.refresh(db_squad)
    return db_squad

def delete_squad(db: Session, squad_id: int):
    db_squad = db.query(models.Squad).filter(models.Squad.id == squad_id).first()
    if db_squad:
        db.delete(db_squad)
        db.commit()
    return db_squad


# Volunteer Status CRUD
def get_volunteer_statuses(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.VolunteerStatus).offset(skip).limit(limit).all()

def create_volunteer_status(db: Session, status: schemas.VolunteerStatusCreate):
    db_status = models.VolunteerStatus(name=status.name, description=status.description)
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

def update_volunteer_status(db: Session, volunteer_id: int, new_status_id: int):
    db_volunteer = db.query(models.Volunteer).filter(models.Volunteer.id == volunteer_id).first()
    if not db_volunteer:
        return None

    # Record current status in history before updating
    current_status_id = db_volunteer.status_id
    if current_status_id != new_status_id:
        status_history_entry = models.VolunteerStatusHistory(
            volunteer_id=volunteer_id,
            status_id=new_status_id # We record the *new* status in the history
        )
        db.add(status_history_entry)

        db_volunteer.status_id = new_status_id

        # Check if new status is ACTIVE and if invite hasn't been sent yet
        active_status = db.query(models.VolunteerStatus).filter(models.VolunteerStatus.name == "ACTIVE").first()
        if active_status and new_status_id == active_status.id:
            if not db_volunteer.discord_invite_sent:
                from app.utils import send_discord_invite_email
                send_discord_invite_email(db_volunteer.email, db_volunteer.name)
                db_volunteer.discord_invite_sent = True

        db.commit()
        db.refresh(db_volunteer)
    return db_volunteer

# Volunteer Type CRUD
def get_volunteer_types(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.VolunteerType).offset(skip).limit(limit).all()

def create_volunteer_type(db: Session, type_data: schemas.VolunteerTypeBase):
    db_type = models.VolunteerType(name=type_data.name, description=type_data.description)
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type

def update_volunteer_type(db: Session, volunteer_id: int, new_type_id: int):
    db_volunteer = db.query(models.Volunteer).filter(models.Volunteer.id == volunteer_id).first()
    if not db_volunteer:
        return None

    if db_volunteer.volunteer_type_id != new_type_id:
        db_volunteer.volunteer_type_id = new_type_id
        db.commit()
        db.refresh(db_volunteer)
    return db_volunteer

def update_volunteer_squad(db: Session, volunteer_id: int, new_squad_id: int):
    db_volunteer = db.query(models.Volunteer).filter(models.Volunteer.id == volunteer_id).first()
    if not db_volunteer:
        return None

    if db_volunteer.squad_id != new_squad_id:
        db_volunteer.squad_id = new_squad_id
        db.commit()
        db.refresh(db_volunteer)
    return db_volunteer

def get_dashboard_stats(db: Session):
    # 1. Group by status
    status_counts = db.query(
        models.VolunteerStatus.name, func.count(models.Volunteer.id)
    ).join(
        models.Volunteer, models.Volunteer.status_id == models.VolunteerStatus.id
    ).group_by(
        models.VolunteerStatus.name
    ).all()
    
    stats_by_status = [{"status": name, "count": count} for name, count in status_counts]
    
    # 2. Group by squad
    squad_counts = db.query(
        models.Squad.name, func.count(models.Volunteer.id)
    ).join(
        models.Volunteer, models.Volunteer.squad_id == models.Squad.id
    ).group_by(
        models.Squad.name
    ).all()

    stats_by_squad = [{"squad": name, "count": count} for name, count in squad_counts]

    # 3. Group by volunteer type
    type_counts = db.query(
        models.VolunteerType.name, func.count(models.Volunteer.id)
    ).join(
        models.Volunteer, models.Volunteer.volunteer_type_id == models.VolunteerType.id
    ).group_by(
        models.VolunteerType.name
    ).all()

    stats_by_type = [{"volunteer_type": name, "count": count} for name, count in type_counts]

    # 4. Registered today (Brasilia)
    try:
        tz_brasilia = ZoneInfo("America/Sao_Paulo")
    except Exception:
         tz_brasilia = timezone(timedelta(hours=-3))

    now_brasilia = datetime.now(tz_brasilia)
    
    # Start of day in Brasilia
    start_of_day_brasilia = now_brasilia.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Convert to UTC for DB query
    start_of_day_utc = start_of_day_brasilia.astimezone(timezone.utc)
    
    count_today = db.query(models.Volunteer).filter(
        models.Volunteer.created_at >= start_of_day_utc
    ).count()

    # 4. Total volunteers
    total_volunteers = db.query(models.Volunteer).count()
    
    return {
        "total_volunteers_by_status": stats_by_status,
        "total_volunteers_by_squad": stats_by_squad,
        "total_volunteers_by_type": stats_by_type,
        "total_volunteers_registered_today": count_today,
        "total_volunteers": total_volunteers
    }

def create_volunteer_edit_token(db: Session, email: str):
    volunteer = get_volunteer_by_email(db, email)
    if not volunteer:
        return None
    
    token = generate_edit_token()
    # Expire in 1 hour. Using UTC for consistency.
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    volunteer.edit_token = token
    volunteer.edit_token_expires_at = expires_at
    db.commit()
    db.refresh(volunteer)
    return volunteer

def get_volunteer_by_token(db: Session, token: str):
    return db.query(models.Volunteer).filter(models.Volunteer.edit_token == token).first()

def update_volunteer_profile_by_token(db: Session, token: str, profile_data: schemas.VolunteerUpdateProfile):
    volunteer = get_volunteer_by_token(db, token)
    if not volunteer:
        return None, "Token inválido"
    
    # Check Expiration
    # Ensure both are offset-aware or both naive. 
    # If DB returns naive, assume UTC if we stored UTC.
    now = datetime.now(timezone.utc)
    if volunteer.edit_token_expires_at:
        expiry = volunteer.edit_token_expires_at
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        
        if expiry < now:
            return None, "Link expirado"
    else:
        return None, "Token inválido"

    # Check Daily Limit
    today = date.today()
    if volunteer.last_edit_date != today:
        volunteer.daily_edits_count = 0
        volunteer.last_edit_date = today
    
    if volunteer.daily_edits_count >= 2:
        return None, "Limite diário de edições atingido (2 alterações por dia)"

    # Update Fields
    if profile_data.name:
        volunteer.name = profile_data.name
    if profile_data.linkedin:
        volunteer.linkedin = profile_data.linkedin
    if profile_data.volunteer_type_id:
        volunteer.volunteer_type_id = profile_data.volunteer_type_id
    
    # Allow updating phone/discord/github to null/empty if passed, or new value
    volunteer.phone = profile_data.phone
    volunteer.discord = profile_data.discord
    volunteer.github = profile_data.github
    
    volunteer.daily_edits_count += 1
    
    db.commit()
    db.refresh(volunteer)
    return volunteer, None


# Project CRUD
def create_project(db: Session, project: schemas.ProjectCreate):
    db_project = models.Project(
        name=project.name,
        description=project.description,
        link=project.link
    )
    
    if project.squad_ids:
        squads = db.query(models.Squad).filter(models.Squad.id.in_(project.squad_ids)).all()
        db_project.squads = squads
        
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Project).options(joinedload(models.Project.squads)).offset(skip).limit(limit).all()


def get_project(db: Session, project_id: int):
    return db.query(models.Project).options(joinedload(models.Project.squads)).filter(models.Project.id == project_id).first()


def delete_project(db: Session, project_id: int):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if db_project:
        db.delete(db_project)
        db.commit()
    return db_project


# Feedback CRUD
def create_feedback(db: Session, feedback: schemas.FeedbackCreate, user_id: int, volunteer_id: int):
    db_feedback = models.Feedback(**feedback.dict(), user_id=user_id, volunteer_id=volunteer_id)
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

def get_feedbacks_for_volunteer(db: Session, volunteer_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Feedback).options(
        joinedload(models.Feedback.author).joinedload(models.User.volunteer)
    ).filter(models.Feedback.volunteer_id == volunteer_id)\
        .order_by(models.Feedback.created_at.desc())\
        .offset(skip).limit(limit).all()

def get_feedback(db: Session, feedback_id: int):
    return db.query(models.Feedback).filter(models.Feedback.id == feedback_id).first()

def update_feedback(db: Session, feedback_id: int, feedback: schemas.FeedbackUpdate):
    db_feedback = db.query(models.Feedback).filter(models.Feedback.id == feedback_id).first()
    if not db_feedback:
        return None
    
    db_feedback.content = feedback.content
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

def delete_feedback(db: Session, feedback_id: int):
    db_feedback = db.query(models.Feedback).filter(models.Feedback.id == feedback_id).first()
    if db_feedback:
        db.delete(db_feedback)
        db.commit()
    return db_feedback


# JobOpening CRUD
def create_job_opening(db: Session, job: schemas.JobOpeningCreate, user_id: int):
    db_job = models.JobOpening(**job.dict(), owner_id=user_id)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def get_job_openings(db: Session, skip: int = 0, limit: int = 100, active_only: bool = False):
    query = db.query(models.JobOpening)
    if active_only:
        query = query.filter(models.JobOpening.is_active == True)
    return query.order_by(models.JobOpening.created_at.desc()).offset(skip).limit(limit).all()


def get_job_opening(db: Session, job_id: int):
    return db.query(models.JobOpening).filter(models.JobOpening.id == job_id).first()


def update_job_opening(db: Session, job_id: int, job: schemas.JobOpeningCreate):
    db_job = db.query(models.JobOpening).filter(models.JobOpening.id == job_id).first()
    if not db_job:
        return None
    
    for key, value in job.dict().items():
        setattr(db_job, key, value)
    
    db.commit()
    db.refresh(db_job)
    return db_job


def delete_job_opening(db: Session, job_id: int):
    db_job = db.query(models.JobOpening).filter(models.JobOpening.id == job_id).first()
    if db_job:
        db.delete(db_job)
        db.commit()
    return db_job


# JobApplication CRUD
def create_job_application(db: Session, application: schemas.JobApplicationCreate):
    # Check if already applied
    existing = db.query(models.JobApplication).filter(
        models.JobApplication.job_id == application.job_id,
        models.JobApplication.volunteer_id == application.volunteer_id
    ).first()
    
    if existing:
        return existing # Or raise error

    db_application = models.JobApplication(**application.dict())
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application


def get_job_applications(db: Session, job_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.JobApplication).filter(models.JobApplication.job_id == job_id)\
        .options(joinedload(models.JobApplication.volunteer))\
        .offset(skip).limit(limit).all()
