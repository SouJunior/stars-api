import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import models, schemas
from app.auth import get_password_hash

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_user_volunteer.db"
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

def test_user_volunteer_relationship_api():
    db = TestingSessionLocal()
    
    # 1. Create User
    email = "test.relation@example.com"
    password = "password123"
    hashed_password = get_password_hash(password)
    user = models.User(email=email, hashed_password=hashed_password, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 2. Login to get token
    response = client.post("/token", data={"username": email, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Check /users/me before volunteer exists
    response = client.get("/users/me/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    # user.volunteer should be None
    assert data.get("volunteer") is None
    
    # 4. Create Volunteer with same email
    job = models.JobTitle(title="Dev", is_active=True)
    db.add(job)
    db.commit()
    db.refresh(job)
    
    vol = models.Volunteer(
        name="Test Relation",
        email=email,
        jobtitle_id=job.id,
        is_active=True
    )
    db.add(vol)
    db.commit()
    
    # 5. Check /users/me after volunteer exists
    response = client.get("/users/me/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data.get("volunteer") is not None
    assert data["volunteer"]["email"] == email
    assert data["volunteer"]["name"] == "Test Relation"

    db.close()
