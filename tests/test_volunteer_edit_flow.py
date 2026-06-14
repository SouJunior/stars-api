import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import models
from datetime import datetime, timedelta, timezone

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_volunteer_edit.db"
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
    yield
    Base.metadata.drop_all(bind=engine)

def test_volunteer_edit_flow():
    db = TestingSessionLocal()
    
    # 1. Setup Data
    job = models.JobTitle(title="Developer", is_active=True)
    db.add(job)
    
    # Create Statuses (Needed for default creation often)
    status_interested = models.VolunteerStatus(name="INTERESTED", description="Interested")
    db.add(status_interested)
    db.commit()

    volunteer = models.Volunteer(
        name="John Doe", 
        email="john@example.com", 
        linkedin="https://linkedin.com/in/john",
        phone="1234567890",
        discord="john#1234",
        jobtitle_id=job.id,
        status_id=status_interested.id
    )
    db.add(volunteer)
    db.commit()
    db.refresh(volunteer)
    
    volunteer_id = volunteer.id
    
    # 2. Request Edit Link
    response = client.post("/volunteers/request-edit-link", json={"email": "john@example.com"})
    assert response.status_code == 200
    assert response.json() == {"message": "Link de edição enviado para o e-mail."}
    
    # Verify Token in DB
    db.refresh(volunteer)
    assert volunteer.edit_token is not None
    token = volunteer.edit_token
    
    # 3. Get Volunteer for Edit (Validate Token)
    response = client.get(f"/volunteers/edit/{token}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    
    # 4. Update Profile
    update_data = {
        "name": "John Updated",
        "linkedin": "https://linkedin.com/in/john-updated",
        "phone": "9876543210",
        "discord": "john_updated#1234"
    }
    response = client.patch(f"/volunteers/edit/{token}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "John Updated"
    assert data["phone"] == "9876543210"
    
    # Verify DB update
    db.refresh(volunteer)
    assert volunteer.name == "John Updated"
    assert volunteer.daily_edits_count == 1
    
    # 5. Second Update (Should succeed)
    update_data_2 = {
        "name": "John Updated Again",
        "linkedin": "https://linkedin.com/in/john-updated",
        "phone": "9876543210",
        "discord": "john_updated#1234"
    }
    response = client.patch(f"/volunteers/edit/{token}", json=update_data_2)
    assert response.status_code == 200
    
    db.refresh(volunteer)
    assert volunteer.daily_edits_count == 2
    
    # 6. Third Update (Should fail)
    update_data_3 = {
        "name": "John Updated Once More",
        "linkedin": "https://linkedin.com/in/john-updated",
        "phone": "9876543210",
        "discord": "john_updated#1234"
    }
    response = client.patch(f"/volunteers/edit/{token}", json=update_data_3)
    assert response.status_code == 400
    assert "Limite diário" in response.json()["detail"]
    
    db.close()

def test_edit_token_expiration():
    db = TestingSessionLocal()
    
    # Setup
    job = models.JobTitle(title="Developer", is_active=True)
    status_interested = models.VolunteerStatus(name="INTERESTED", description="Interested")
    db.add(job)
    db.add(status_interested)
    db.commit()

    volunteer = models.Volunteer(
        name="Jane Doe", 
        email="jane@example.com", 
        linkedin="https://linkedin.com/in/jane",
        jobtitle_id=job.id,
        status_id=status_interested.id
    )
    db.add(volunteer)
    db.commit()
    
    # Manually set an expired token
    expired_token = "expired_token_123"
    volunteer.edit_token = expired_token
    # Use timezone-aware UTC datetime
    volunteer.edit_token_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db.commit()
    
    # Try to access
    response = client.get(f"/volunteers/edit/{expired_token}")
    assert response.status_code == 400
    assert "Link expirado" in response.json()["detail"]
    
    # Try to update
    response = client.patch(f"/volunteers/edit/{expired_token}", json={
        "name": "Should Fail",
        "linkedin": "l",
        "phone": "p",
        "discord": "d"
    })
    assert response.status_code == 400
    assert "Link expirado" in response.json()["detail"]
    
    db.close()
