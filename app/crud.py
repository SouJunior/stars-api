from sqlalchemy.orm import Session, joinedload
from sqlalchemy import create_engine, Column, Integer, String, Boolean, func
from . import models, schemas
from app.auth import get_password_hash
from datetime import datetime, timedelta, timezone

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

def get_volunteers(db: Session, skip: int = 0, limit: int = 100, name: str = None, email: str = None, jobtitle_id: int = None, status_id: int = None, order: str = "desc"):
    query = db.query(models.Volunteer).options(
        joinedload(models.Volunteer.jobtitle),
        joinedload(models.Volunteer.status),
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

    if order == "desc":
        query = query.order_by(models.Volunteer.created_at.desc())
    else:
        query = query.order_by(models.Volunteer.created_at.asc())

    return query.offset(skip).limit(limit).all()

def get_volunteer_by_id(db: Session, volunteer_id: int):
    return db.query(models.Volunteer).options(
        joinedload(models.Volunteer.jobtitle),
        joinedload(models.Volunteer.status),
        joinedload(models.Volunteer.status_history).joinedload(models.VolunteerStatusHistory.status)
    ).filter(models.Volunteer.id == volunteer_id).first()

def get_volunteer_by_email(db: Session, email: str):
    return db.query(models.Volunteer)\
        .options(
            joinedload(models.Volunteer.jobtitle),
            joinedload(models.Volunteer.status),
            joinedload(models.Volunteer.status_history).joinedload(models.VolunteerStatusHistory.status)
        )\
        .filter(models.Volunteer.email == email).first()

def create_volunteer(db: Session, volunteer: schemas.VolunteerCreate, jobtitle_id: int):
    # Get default status "INTERESTED"
    default_status = db.query(models.VolunteerStatus).filter(models.VolunteerStatus.name == "INTERESTED").first()
    if not default_status:
        raise ValueError("Default status 'INTERESTED' not found.")

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
    
    # 2. Registered today (Brasilia)
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
    
    return {
        "total_volunteers_by_status": stats_by_status,
        "total_volunteers_registered_today": count_today
    }