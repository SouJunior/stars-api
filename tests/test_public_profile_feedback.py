import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import models
from datetime import datetime

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_public_profile_feedback.db"
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

def test_public_profile_feedback_with_author_details():
    db = TestingSessionLocal()
    
    # Setup dependencies
    job = models.JobTitle(title="Dev", is_active=True)
    db.add(job)
    status = models.VolunteerStatus(name="ACTIVE")
    db.add(status)
    db.commit()

    # 1. Receiver Volunteer
    receiver = models.Volunteer(
        name="Receiver",
        email="receiver@example.com",
        linkedin="link",
        jobtitle_id=job.id,
        status_id=status.id
    )
    db.add(receiver)
    db.commit()
    
    # 2. Author with Volunteer Profile
    author_user = models.User(email="author@example.com", hashed_password="pw")
    db.add(author_user)
    db.commit()
    
    author_vol = models.Volunteer(
        name="Author Name",
        email="author@example.com", # Matches user email
        linkedin="https://linkedin.com/in/author",
        jobtitle_id=job.id,
        status_id=status.id
    )
    db.add(author_vol)
    db.commit()

    # 3. Author WITHOUT Volunteer Profile
    anon_user = models.User(email="anon@example.com", hashed_password="pw")
    db.add(anon_user)
    db.commit()
    
    # 4. Feedbacks
    feedback1 = models.Feedback(
        content="Great work!",
        user_id=author_user.id,
        volunteer_id=receiver.id
    )
    feedback2 = models.Feedback(
        content="Good job!",
        user_id=anon_user.id,
        volunteer_id=receiver.id
    )
    db.add(feedback1)
    db.add(feedback2)
    db.commit()
    
    receiver_id = receiver.id
    db.close()
    
    # 5. Test
    response = client.get(f"/volunteers/{receiver_id}/public")
    assert response.status_code == 200
    data = response.json()
    
    feedbacks = data["feedbacks"]
    assert len(feedbacks) == 2
    
    # Sort feedbacks by id or content to be sure which is which, 
    # though usually order is desc created_at. Since created at same time, order might be unstable or by ID.
    
    f1 = next(f for f in feedbacks if f["content"] == "Great work!")
    assert f1["author_name"] == "Author Name"
    assert f1["author_linkedin"] == "https://linkedin.com/in/author"
    
    f2 = next(f for f in feedbacks if f["content"] == "Good job!")
    assert f2["author_name"] == "***"
    assert f2["author_linkedin"] is None

