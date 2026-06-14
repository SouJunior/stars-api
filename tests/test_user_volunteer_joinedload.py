import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from app.main import app
from app.database import Base, get_db
from app import models, utils
from app.auth import get_password_hash

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_user_volunteer_joinedload.db"
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

@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_get_user_by_email_includes_volunteer():
    db = TestingSessionLocal()
    
    # 1. Create User
    email = "wouerner@soujunior.tech"
    password = "password123"
    hashed_password = get_password_hash(password)
    user = models.User(email=email, hashed_password=hashed_password, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 2. Create Volunteer with same email
    job = models.JobTitle(title="Dev", is_active=True)
    db.add(job)
    db.commit()
    db.refresh(job)
    
    vol = models.Volunteer(
        name="Wouerner Volunteer",
        email=email,
        jobtitle_id=job.id,
        is_active=True
    )
    db.add(vol)
    db.commit()
    
    # 3. Test utils.get_user_by_email
    # We close and reopen session to ensure no lazy loading from previous objects
    db.close()
    db = TestingSessionLocal()
    
    fetched_user = utils.get_user_by_email(db, email)
    
    assert fetched_user is not None
    assert fetched_user.email == email
    # Check if volunteer is loaded
    assert fetched_user.volunteer is not None
    assert fetched_user.volunteer.name == "Wouerner Volunteer"
    
    db.close()
