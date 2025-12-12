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

def get_volunteers(db: Session, skip: int = 0, limit: int = 100, name: str = None, email: str = None, jobtitle_id: int = None, status_id: int = None, squad_id: int = None, order: str = "desc"):
    query = db.query(models.Volunteer).options(
        joinedload(models.Volunteer.jobtitle),
        joinedload(models.Volunteer.status),
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
        joinedload(models.Volunteer.squad),
        joinedload(models.Volunteer.status_history).joinedload(models.VolunteerStatusHistory.status)
    ).filter(models.Volunteer.id == volunteer_id).first()

def get_volunteer_by_email(db: Session, email: str):
    return db.query(models.Volunteer)\
        .options(
            joinedload(models.Volunteer.jobtitle),
            joinedload(models.Volunteer.status),
            joinedload(models.Volunteer.squad),
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


# Squad CRUD
def get_squads(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Squad).offset(skip).limit(limit).all()

def create_squad(db: Session, squad: schemas.SquadCreate):
    db_squad = models.Squad(name=squad.name)
    db.add(db_squad)
    db.commit()
    db.refresh(db_squad)
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

    # 3. Registered today (Brasilia)
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
    # Allow updating phone/discord to null/empty if passed, or new value
    volunteer.phone = profile_data.phone
    volunteer.discord = profile_data.discord
    
    volunteer.daily_edits_count += 1
    
    db.commit()
    db.refresh(volunteer)
    return volunteer, None