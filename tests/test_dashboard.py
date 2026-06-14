import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
from app.main import app, get_current_active_user
from app.database import Base, get_db
from app import models, schemas

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_dashboard.db"
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

# Mock authenticated user
def override_get_current_active_user():
    return schemas.User(
        id=1, email="admin@example.com", is_active=True, items=[]
    )

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_active_user] = override_get_current_active_user

client = TestClient(app)

@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_dashboard_stats():
    db = TestingSessionLocal()
    
    # Create Job Title
    job = models.JobTitle(title="Dev", is_active=True)
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Create Statuses
    s1 = models.VolunteerStatus(name="INTERESTED", description="Interested")
    s2 = models.VolunteerStatus(name="APPROVED", description="Approved")
    db.add_all([s1, s2])
    db.commit()
    db.refresh(s1)
    db.refresh(s2)

    # Create Squads
    sq1 = models.Squad(name="Alpha")
    sq2 = models.Squad(name="Beta")
    db.add_all([sq1, sq2])
    db.commit()
    db.refresh(sq1)
    db.refresh(sq2)
    
    # Create Volunteers
    # 1. Old volunteer (yesterday) - Squad Alpha
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    v1 = models.Volunteer(
        name="Old Vol", email="old@ex.com", linkedin="l1", 
        jobtitle_id=job.id, status_id=s1.id, squad_id=sq1.id,
        created_at=yesterday
    )
    
    # 2. Today volunteer (now) - Squad Alpha
    # Explicitly set created_at to now(utc) to avoid ambiguity with server defaults in sqlite
    now_utc = datetime.now(timezone.utc)
    v2 = models.Volunteer(
        name="New Vol", email="new@ex.com", linkedin="l2", 
        jobtitle_id=job.id, status_id=s1.id, squad_id=sq1.id,
        created_at=now_utc
    )
    
    # 3. Another Today volunteer (different status) - Squad Beta
    v3 = models.Volunteer(
        name="Approved Vol", email="app@ex.com", linkedin="l3", 
        jobtitle_id=job.id, status_id=s2.id, squad_id=sq2.id,
        created_at=now_utc
    )
    
    db.add_all([v1, v2, v3])
    db.commit()
    db.close()
    
    # Call endpoint
    response = client.get("/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    
    # Verify counts by status
    # We have 2 INTERESTED (v1, v2) and 1 APPROVED (v3)
    status_counts = {item['status']: item['count'] for item in data['total_volunteers_by_status']}
    assert status_counts["INTERESTED"] == 2
    assert status_counts["APPROVED"] == 1

    # Verify counts by squad
    # We have 2 Alpha (v1, v2) and 1 Beta (v3)
    squad_counts = {item['squad']: item['count'] for item in data['total_volunteers_by_squad']}
    assert squad_counts["Alpha"] == 2
    assert squad_counts["Beta"] == 1
    
    # Verify today count
    # v2 and v3 are today. v1 is yesterday. Total 2.
    assert data['total_volunteers_registered_today'] == 2

    # Verify total volunteers
    assert data['total_volunteers'] == 3
