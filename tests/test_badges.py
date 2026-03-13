import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import models, schemas
from app.auth import get_password_hash

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_badges.db"
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

def get_token(email, password, role=models.UserRole.MENTOR):
    # Create user with role
    db = TestingSessionLocal()
    user = models.User(email=email, hashed_password=get_password_hash(password), role=role)
    db.add(user)
    db.commit()
    db.close()

    response = client.post(
        "/token",
        data={"username": email, "password": password},
    )
    return response.json()["access_token"]

def test_award_badge_unauthorized():
    response = client.post(
        "/volunteers/1/badges",
        json={"title": "Star", "description": "Good job", "volunteer_id": 1}
    )
    assert response.status_code == 401

def test_award_badge_success():
    db = TestingSessionLocal()
    # Setup jobtitle and volunteer
    job = models.JobTitle(title="Dev", is_active=True)
    db.add(job)
    db.commit()
    volunteer = models.Volunteer(name="Vol", email="vol@example.com", linkedin="link", jobtitle_id=job.id)
    db.add(volunteer)
    db.commit()
    v_id = volunteer.id
    db.close()

    token = get_token("mentor@example.com", "password", role=models.UserRole.MENTOR)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        f"/volunteers/{v_id}/badges",
        json={"title": "Excellence", "description": "Outstanding contribution", "volunteer_id": v_id},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Excellence"
    assert data["description"] == "Outstanding contribution"
    assert data["volunteer_id"] == v_id

def test_list_badges():
    db = TestingSessionLocal()
    job = models.JobTitle(title="Dev", is_active=True)
    db.add(job)
    db.commit()
    volunteer = models.Volunteer(name="Vol", email="vol@example.com", linkedin="link", jobtitle_id=job.id)
    db.add(volunteer)
    db.commit()
    
    user = models.User(email="issuer@example.com", hashed_password=get_password_hash("pass"), role=models.UserRole.MENTOR)
    db.add(user)
    db.commit()

    badge = models.Badge(title="Super", volunteer_id=volunteer.id, issuer_id=user.id)
    db.add(badge)
    db.commit()
    
    v_id = volunteer.id
    db.close()

    # Logged in user required to see badges
    token = get_token("viewer@example.com", "pass")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"/volunteers/{v_id}/badges", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Super"

def test_delete_badge_unauthorized():
    db = TestingSessionLocal()
    job = models.JobTitle(title="Dev", is_active=True)
    db.add(job)
    db.commit()
    volunteer = models.Volunteer(name="Vol", email="vol@example.com", linkedin="link", jobtitle_id=job.id)
    db.add(volunteer)
    db.commit()
    
    issuer = models.User(email="issuer@example.com", hashed_password=get_password_hash("pass"), role=models.UserRole.MENTOR)
    db.add(issuer)
    db.commit()

    badge = models.Badge(title="To delete", volunteer_id=volunteer.id, issuer_id=issuer.id)
    db.add(badge)
    db.commit()
    
    b_id = badge.id
    db.close()

    # Different user tries to delete
    token = get_token("other@example.com", "pass", role=models.UserRole.MENTOR)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete(f"/badges/{b_id}", headers=headers)
    assert response.status_code == 403

def test_delete_badge_success_by_author():
    db = TestingSessionLocal()
    job = models.JobTitle(title="Dev", is_active=True)
    db.add(job)
    db.commit()
    volunteer = models.Volunteer(name="Vol", email="vol@example.com", linkedin="link", jobtitle_id=job.id)
    db.add(volunteer)
    db.commit()
    
    issuer = models.User(email="issuer@example.com", hashed_password=get_password_hash("pass"), role=models.UserRole.MENTOR)
    db.add(issuer)
    db.commit()

    badge = models.Badge(title="To delete", volunteer_id=volunteer.id, issuer_id=issuer.id)
    db.add(badge)
    db.commit()
    
    b_id = badge.id
    db.close()

    token = get_token("issuer@example.com", "pass", role=models.UserRole.MENTOR)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.delete(f"/badges/{b_id}", headers=headers)
    assert response.status_code == 200
    
    # Verify deleted
    db = TestingSessionLocal()
    assert db.query(models.Badge).filter(models.Badge.id == b_id).first() is None
    db.close()
