import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import models

# Configuração do banco de dados de teste em memória
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_squads.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Sobrescreve a dependência get_db para usar o banco de dados de teste
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Pre-populate required data
    db = TestingSessionLocal()
    
    # Create JobTitle
    job_title = models.JobTitle(title="Developer", is_active=True)
    db.add(job_title)
    
    # Create Default Status
    status = models.VolunteerStatus(name="INTERESTED", description="Interested")
    db.add(status)
    
    # Create Admin User for Auth
    from app.crud import create_user
    from app.schemas import UserCreate
    user_in = UserCreate(email="admin@example.com", password="password", registration_code="changeme")
    create_user(db, user_in)
    
    db.commit()
    db.close()
    
    yield
    
    Base.metadata.drop_all(bind=engine)

def get_auth_headers():
    response = client.post(
        "/token",
        data={"username": "admin@example.com", "password": "password"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_squad():
    headers = get_auth_headers()
    response = client.post(
        "/squads/",
        json={"name": "Alpha Squad"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Alpha Squad"
    assert "id" in data
    return data["id"]

def test_get_squads():
    headers = get_auth_headers()
    # Create another squad
    client.post("/squads/", json={"name": "Beta Squad"}, headers=headers)
    
    response = client.get("/squads/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    names = [s["name"] for s in data]
    assert "Alpha Squad" in names
    assert "Beta Squad" in names

def test_volunteer_with_squad():
    headers = get_auth_headers()
    
    # Get Squad ID (Alpha Squad created in first test)
    squads = client.get("/squads/", headers=headers).json()
    alpha_squad = next(s for s in squads if s["name"] == "Alpha Squad")
    squad_id = alpha_squad["id"]
    
    # Get JobTitle ID
    jobtitles = client.get("/jobtitles/").json()
    jobtitle_id = jobtitles[0]["id"]
    
    # Create Volunteer with Squad
    response = client.post(
        "/volunteer",
        json={
            "name": "Soldier Boy",
            "email": "soldier@example.com",
            "linkedin": "linkedin.com/soldier",
            "jobtitle_id": jobtitle_id,
            "squad_id": squad_id
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["squad_id"] == squad_id
    assert data["squad"]["name"] == "Alpha Squad"

def test_volunteer_without_squad():
    # Get JobTitle ID
    jobtitles = client.get("/jobtitles/").json()
    jobtitle_id = jobtitles[0]["id"]
    
    # Create Volunteer without Squad
    response = client.post(
        "/volunteer",
        json={
            "name": "Lone Wolf",
            "email": "lonewolf@example.com",
            "linkedin": "linkedin.com/lonewolf",
            "jobtitle_id": jobtitle_id
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["squad_id"] is None
    assert data["squad"] is None

def test_filter_volunteers_by_squad():
    headers = get_auth_headers()
    
    # Get Squad ID (Alpha Squad)
    squads = client.get("/squads/", headers=headers).json()
    alpha_squad = next(s for s in squads if s["name"] == "Alpha Squad")
    squad_id = alpha_squad["id"]
    
    # Filter by Squad
    response = client.get(f"/volunteers/?squad_id={squad_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # Should find "Soldier Boy" but not "Lone Wolf"
    found_emails = [v["email"] for v in data]
    assert "soldier@example.com" in found_emails
    assert "lonewolf@example.com" not in found_emails

def test_filter_volunteers_by_empty_squad():
    headers = get_auth_headers()
    
    # Filter by non-existent Squad
    response = client.get("/volunteers/?squad_id=99999", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0
