import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import models

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_volunteer_privacy.db"
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

def test_get_volunteer_by_email_hides_phone():
    db = TestingSessionLocal()
    
    # Create Job Title
    job = models.JobTitle(title="Developer", is_active=True)
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Create Volunteer with phone
    vol = models.Volunteer(
        name="Privacy Tester",
        email="privacy@example.com",
        linkedin="https://linkedin.com/in/privacy",
        phone="+1234567890",
        jobtitle_id=job.id,
        is_active=True
    )
    db.add(vol)
    db.commit()
    db.close()

    # Call endpoint
    response = client.get("/volunteer/privacy@example.com")
    assert response.status_code == 200
    data = response.json()
    
    # Verify phone is NOT present
    assert "phone" not in data
    assert data["name"] == "Privacy Tester"
    assert data["email"] == "privacy@example.com"

def test_get_volunteer_by_id_shows_phone():
    db = TestingSessionLocal()
    
    # Create Job Title
    job = models.JobTitle(title="Developer2", is_active=True)
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Create Volunteer with phone
    vol = models.Volunteer(
        name="Public Tester",
        email="public@example.com",
        linkedin="https://linkedin.com/in/public",
        phone="+0987654321",
        jobtitle_id=job.id,
        is_active=True
    )
    db.add(vol)
    db.commit()
    vol_id = vol.id
    db.close()

    # Call endpoint
    response = client.get(f"/volunteers/{vol_id}")
    assert response.status_code == 200
    data = response.json()
    
    # Verify phone IS present (assuming other endpoints should still return it)
    assert "phone" in data
    assert data["phone"] == "+0987654321"
