import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import models

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_volunteers_status_search.db"
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

def test_search_volunteers_by_status():
    db = TestingSessionLocal()
    
    # Create Job Title
    dev_job = models.JobTitle(title="Developer", is_active=True)
    db.add(dev_job)
    db.commit()
    db.refresh(dev_job)
    
    # Create Statuses
    status_active = models.VolunteerStatus(name="ACTIVE", description="Active volunteer")
    status_inactive = models.VolunteerStatus(name="INACTIVE", description="Inactive volunteer")
    db.add(status_active)
    db.add(status_inactive)
    db.commit()
    db.refresh(status_active)
    db.refresh(status_inactive)
    
    # Create Volunteers
    v1 = models.Volunteer(name="Alice", email="alice@example.com", linkedin="l1", jobtitle_id=dev_job.id, status_id=status_active.id)
    v2 = models.Volunteer(name="Bob", email="bob@example.com", linkedin="l2", jobtitle_id=dev_job.id, status_id=status_inactive.id)
    v3 = models.Volunteer(name="Charlie", email="charlie@example.com", linkedin="l3", jobtitle_id=dev_job.id, status_id=status_active.id)
    db.add_all([v1, v2, v3])
    db.commit()
    db.close()

    # Test Search by Status ID (Active)
    response = client.get(f"/volunteers/?status_id={status_active.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = [v["name"] for v in data]
    assert "Alice" in names
    assert "Charlie" in names
    assert "Bob" not in names

    # Test Search by Status ID (Inactive)
    response = client.get(f"/volunteers/?status_id={status_inactive.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Bob"

    # Test Search by Status ID (Non-existent)
    response = client.get(f"/volunteers/?status_id=999")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0
