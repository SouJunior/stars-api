import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import models

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_volunteers_search_email.db"
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

def test_search_volunteers_by_email():
    db = TestingSessionLocal()
    
    # Create Job Titles
    dev_job = models.JobTitle(title="Developer", is_active=True)
    db.add(dev_job)
    db.commit()
    db.refresh(dev_job)
    
    dev_job_id = dev_job.id
    
    # Create Volunteers
    v1 = models.Volunteer(name="Alice", email="alice@example.com", linkedin="l1", jobtitle_id=dev_job_id)
    v2 = models.Volunteer(name="Bob", email="bob@example.com", linkedin="l2", jobtitle_id=dev_job_id)
    v3 = models.Volunteer(name="Charlie", email="charlie@company.com", linkedin="l3", jobtitle_id=dev_job_id)
    db.add_all([v1, v2, v3])
    db.commit()
    db.close()

    # Test Search by exact Email
    response = client.get("/volunteers/?email=alice@example.com")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == "alice@example.com"
    assert data[0]["name"] == "Alice"

    # Test Search by partial Email
    response = client.get("/volunteers/?email=example.com")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    emails = [v["email"] for v in data]
    assert "alice@example.com" in emails
    assert "bob@example.com" in emails

    # Test Case Insensitive Email
    response = client.get("/volunteers/?email=ALICE@EXAMPLE.COM")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == "alice@example.com"

    # Test Search by Name AND Email
    response = client.get("/volunteers/?name=Alice&email=alice@example.com")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Alice"

    # Test No Results
    response = client.get("/volunteers/?email=notfound@example.com")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0
