from sqlalchemy.orm import Session, joinedload
from sqlalchemy import create_engine, Column, Integer, String, Boolean, func
from . import models, schemas
from app.auth import get_password_hash


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

def get_volunteers(db: Session, skip: int = 0, limit: int = 100, name: str = None, jobtitle_id: int = None, status_id: int = None):
    query = db.query(models.Volunteer).options(
        joinedload(models.Volunteer.jobtitle),
        joinedload(models.Volunteer.status),
        joinedload(models.Volunteer.status_history).joinedload(models.VolunteerStatusHistory.status)
    )
    if name:
        query = query.filter(models.Volunteer.name.ilike(f"%{name}%"))
    if jobtitle_id:
        query = query.filter(models.Volunteer.jobtitle_id == jobtitle_id)
    if status_id:
        query = query.filter(models.Volunteer.status_id == status_id)
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
