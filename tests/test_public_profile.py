import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import models
from datetime import datetime

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_public_profile.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_get_public_profile_endpoint():
    db = TestingSessionLocal()
    
    # 1. Setup Data
    job = models.JobTitle(title="Developer", is_active=True)
    db.add(job)
    
    squad = models.Squad(name="Alpha Squad")
    db.add(squad)
    
    status = models.VolunteerStatus(name="ACTIVE", description="Active member")
    db.add(status)
    
    db.commit()
    db.refresh(job)
    db.refresh(squad)
    db.refresh(status)
    
    vol = models.Volunteer(
        name="John Public",
        email="john.public@example.com",
        linkedin="https://linkedin.com/in/johnpublic",
        phone="+1234567890",
        discord="john#1234",
        jobtitle_id=job.id,
        squad_id=squad.id,
        status_id=status.id,
        is_active=True
    )
    db.add(vol)
    db.commit()
    db.refresh(vol)

    # Add History
    history = models.VolunteerStatusHistory(
        volunteer_id=vol.id,
        status_id=status.id,
        created_at=datetime.now()
    )
    db.add(history)
    db.commit()
    
    vol_id = vol.id
    db.close()

    # 2. Call Endpoint
    response = client.get(f"/volunteers/{vol_id}/public")
    
    # 3. Assertions
    assert response.status_code == 200
    data = response.json()
    
    # Check Sensitive Data is HIDDEN
    assert "phone" not in data or data["phone"] is None
    # Note: Pydantic model might output 'email' key if it's in the base but excluded? 
    # Let's check schemas.py again. VolunteerPublic inherits VolunteerCommon.
    # VolunteerCommon has: name, linkedin, is_active.
    # VolunteerPublic ADDS: id, jobtitle_id, status_id, squad_id, masked_email, created_at, jobtitle, status, squad, status_history, discord.
    # It does NOT inherit from VolunteerBase (which has phone, email).
    # So 'phone' and 'email' keys should strictly NOT be in the response dict if using Pydantic correctly.
    assert "phone" not in data
    # VolunteerPublic does NOT have 'email' field defined.
    assert "email" not in data
    
    # Check Public Data is PRESENT
    assert data["name"] == "John Public"
    assert data["linkedin"] == "https://linkedin.com/in/johnpublic"
    assert data["discord"] == "john#1234"
    assert data["masked_email"] == "***@example.com"
    
    # Check Relations
    assert data["squad"]["name"] == "Alpha Squad"
    assert data["status"]["name"] == "ACTIVE"
    assert data["jobtitle"]["title"] == "Developer"
    
    # Check History
    assert len(data["status_history"]) >= 1
    assert data["status_history"][0]["status"]["name"] == "ACTIVE"

