import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import models

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_volunteer_phone.db"
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
    Base.metadata.create_all(bind=engine)
    # Ensure INTERESTED status exists for creation
    db = TestingSessionLocal()
    if not db.query(models.VolunteerStatus).filter(models.VolunteerStatus.name == "INTERESTED").first():
        db.add(models.VolunteerStatus(name="INTERESTED", description="Default status"))
        db.commit()
    db.close()
    
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_and_get_volunteer_with_phone():
    db = TestingSessionLocal()
    
    # Create Job Title
    job = models.JobTitle(title="Developer", is_active=True)
    db.add(job)
    db.commit()
    db.refresh(job)
    job_id = job.id
    db.close()

    # Test Create Volunteer with Phone
    payload = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "linkedin": "linkedin.com/in/johndoe",
        "phone": "123-456-7890",
        "jobtitle_id": job_id
    }
    
    response = client.post("/volunteer", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["phone"] == "123-456-7890"
    volunteer_id = data["id"]

    # Test Get Volunteer by ID
    response = client.get(f"/volunteers/{volunteer_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "123-456-7890"

    # Test Get Volunteer List
    response = client.get("/volunteers/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["phone"] == "123-456-7890"

def test_create_volunteer_without_phone():
    db = TestingSessionLocal()
    
    # Create Job Title
    job = models.JobTitle(title="Designer", is_active=True)
    db.add(job)
    db.commit()
    db.refresh(job)
    job_id = job.id
    db.close()

    # Test Create Volunteer without Phone
    payload = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "linkedin": "linkedin.com/in/janedoe",
        "jobtitle_id": job_id
    }
    
    response = client.post("/volunteer", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["phone"] is None
