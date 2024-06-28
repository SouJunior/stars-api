from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String, Boolean, func
from . import models, schemas
from app.auth import get_password_hash


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
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

def get_volunteers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(
    models.Volunteer.id,
    models.Volunteer.name,
    func.replace(
        models.Volunteer.email, 
        func.substr(models.Volunteer.email, 1, func.instr(models.Volunteer.email, '@') - 1),
        '***').label("masked_email"),
    models.Volunteer.is_active,
    models.Volunteer.jobtitle_id,
    # models.Volunteer.email
    ).all()
    # return db.query(models.Volunteer).offset(skip).limit(limit).all()


def get_volunteers_by_email(db: Session, skip: int = 0, limit: int = 100, email: str = ''):
    return db.query(
    models.Volunteer.id,
    models.Volunteer.name,
    func.replace(
        models.Volunteer.email, 
        func.substr(models.Volunteer.email, 1, func.instr(models.Volunteer.email, '@') - 1),
        '***').label("masked_email"),
    models.Volunteer.is_active,
    models.Volunteer.jobtitle_id,
    ).filter(models.Volunteer.email == email).first()


def create_volunteer(db: Session, volunteer: schemas.VolunteerBase, jobtitle_id: int):
    db_volunteer = models.Volunteer(**volunteer.dict())
    db.add(db_volunteer)
    db.commit()
    db.refresh(db_volunteer)
    return db_volunteer


def get_jobtitles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.JobTitle).offset(skip).limit(limit).all()


def get_volunteer_by_email(db: Session, email: str):
    return db.query(models.Volunteer).filter(models.Volunteer.email == email).first()