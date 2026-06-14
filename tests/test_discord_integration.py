import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import models, crud
from unittest.mock import patch

# Use a separate in-memory SQLite db
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_discord.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def seed_data(db):
    # Seed statuses
    statuses = [
        {"name": "INTERESTED", "description": "Interested"},
        {"name": "ACTIVE", "description": "Active"},
    ]
    for s in statuses:
        if not db.query(models.VolunteerStatus).filter_by(name=s["name"]).first():
            db.add(models.VolunteerStatus(**s))
    
    # Seed jobtitle
    if not db.query(models.JobTitle).filter_by(title="Dev").first():
        db.add(models.JobTitle(title="Dev", is_active=True))
    
    db.commit()

@pytest.fixture(scope="function", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_data(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

def test_discord_invite_sent_only_once():
    db = TestingSessionLocal()
    job = db.query(models.JobTitle).first()
    status_interested = db.query(models.VolunteerStatus).filter_by(name="INTERESTED").first()
    status_active = db.query(models.VolunteerStatus).filter_by(name="ACTIVE").first()

    # Create volunteer
    volunteer = models.Volunteer(
        name="Discord Tester",
        email="discord@test.com",
        jobtitle_id=job.id,
        status_id=status_interested.id,
        discord_invite_sent=False
    )
    db.add(volunteer)
    db.commit()
    db.refresh(volunteer)
    volunteer_id = volunteer.id

    with patch("app.utils.send_discord_invite_email") as mock_send:
        # 1. Transition to ACTIVE - should send email
        crud.update_volunteer_status(db, volunteer_id, status_active.id)
        assert mock_send.called is True
        assert mock_send.call_count == 1
        
        # Reload volunteer to check flag
        db.refresh(volunteer)
        assert volunteer.discord_invite_sent is True

        # 2. Transition to INTERESTED and then to ACTIVE again - should NOT send email
        crud.update_volunteer_status(db, volunteer_id, status_interested.id)
        mock_send.reset_mock()
        
        crud.update_volunteer_status(db, volunteer_id, status_active.id)
        assert mock_send.called is False
        assert mock_send.call_count == 0
