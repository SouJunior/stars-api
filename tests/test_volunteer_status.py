import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import models

# Use a separate in-memory SQLite db for this test file to avoid collisions
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_status.db"
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

def seed_statuses(db):
    statuses = [
        {"name": "INTERESTED", "description": "Volunteer expressed interest."},
        {"name": "CONTACTED", "description": "Volunteer has been contacted."},
        {"name": "SCREENING", "description": "Volunteer is undergoing screening."},
        {"name": "ACTIVE", "description": "Volunteer is active."},
        {"name": "INACTIVE", "description": "Volunteer is inactive."},
    ]
    for status_data in statuses:
        if not db.query(models.VolunteerStatus).filter_by(name=status_data["name"]).first():
            db_status = models.VolunteerStatus(
                name=status_data["name"],
                description=status_data["description"]
            )
            db.add(db_status)
    db.commit()

@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=engine)
    
    # Seed statuses
    db = TestingSessionLocal()
    seed_statuses(db)
    db.close()
    
    yield
    Base.metadata.drop_all(bind=engine)

def test_volunteer_status_flow():
    # 1. Create JobTitle (dependency)
    db = TestingSessionLocal()
    job = models.JobTitle(title="Developer", is_active=True)
    db.add(job)
    db.commit()
    db.refresh(job)
    job_id = job.id
    db.close()

    # 2. Create Volunteer
    # Note: status_id is NOT provided
    volunteer_data = {
        "name": "Test Volunteer",
        "email": "volunteer@test.com",
        "linkedin": "http://linkedin.com/in/test",
        "jobtitle_id": job_id,
        "is_active": True
    }
    
    # Using the endpoint
    response = client.post("/volunteer", json=volunteer_data)
    assert response.status_code == 200, response.text
    data = response.json()
    volunteer_id = data["id"]
    
    # 3. Verify Default Status
    assert data["status"]["name"] == "INTERESTED"
    assert len(data["status_history"]) == 1
    assert data["status_history"][0]["status"]["name"] == "INTERESTED"

    # 4. Update Status to CONTACTED (This requires auth if the endpoint is protected)
    # Let's check main.py again. 
    # @app.patch("/volunteers/{volunteer_id}/status/", ...) uses Depends(get_current_active_user)
    # So we CANNOT test status update without auth.
    # BUT the user only asked to verify "create volunteer start with interested status".
    # So steps 1-3 are sufficient to answer the user request!