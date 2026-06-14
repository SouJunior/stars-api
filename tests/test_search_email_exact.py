import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import models

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_search_email.db"
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

def test_search_volunteers_by_email():
    db = TestingSessionLocal()
    
    # Setup Data
    job = models.JobTitle(title="Developer", is_active=True)
    db.add(job)
    db.commit()
    db.refresh(job)
    
    vol1 = models.Volunteer(
        name="Target Volunteer",
        email="target@example.com",
        jobtitle_id=job.id,
        is_active=True
    )
    vol2 = models.Volunteer(
        name="Other Volunteer",
        email="other@example.com",
        jobtitle_id=job.id,
        is_active=True
    )
    # Similar email prefix
    vol3 = models.Volunteer(
        name="Target Like Volunteer",
        email="target.secondary@example.com",
        jobtitle_id=job.id,
        is_active=True
    )

    db.add(vol1)
    db.add(vol2)
    db.add(vol3)
    db.commit()
    db.close()

    # Call Endpoint with email
    response = client.get("/volunteers/?email=target@example.com")
    
    assert response.status_code == 200
    data = response.json()
    
    # It might return vol1 and vol3 because of ilike, so we check if the target is in the list
    assert isinstance(data, list)
    assert len(data) >= 1
    
    found_emails = [v["email"] for v in data]
    assert "target@example.com" in found_emails
    
    # Frontend logic filters for exact match:
    # const match = response.find(v => v.email === email);
    match = next((v for v in data if v["email"] == "target@example.com"), None)
    assert match is not None
    assert match["name"] == "Target Volunteer"

