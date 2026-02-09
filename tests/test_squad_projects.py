import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import models, schemas

# Configuração do banco de dados de teste em memória
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_squad_projects.db"
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

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    # Create Admin User for Auth
    from app.crud import create_user
    # Using a known registration code from settings or default
    user_in = schemas.UserCreate(email="admin@example.com", password="password", registration_code="changeme")
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

def test_squad_with_projects():
    headers = get_auth_headers()
    
    # 1. Create a Squad
    squad_resp = client.post("/squads/", json={"name": "Project Squad", "description": "Testing projects"}, headers=headers)
    assert squad_resp.status_code == 200
    squad_id = squad_resp.json()["id"]
    
    # 2. Create Projects and associate with Squad
    project1_resp = client.post("/projects/", json={"name": "Project 1", "description": "Desc 1", "squad_ids": [squad_id]}, headers=headers)
    assert project1_resp.status_code == 200
    
    project2_resp = client.post("/projects/", json={"name": "Project 2", "description": "Desc 2", "squad_ids": [squad_id]}, headers=headers)
    assert project2_resp.status_code == 200
    
    # 3. Get Squad details and verify projects
    response = client.get(f"/squads/{squad_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["projects_count"] == 2
    assert len(data["projects"]) == 2
    project_names = [p["name"] for p in data["projects"]]
    assert "Project 1" in project_names
    assert "Project 2" in project_names

def test_squads_list_with_projects_count():
    headers = get_auth_headers()
    
    response = client.get("/squads/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    squad = next(s for s in data if s["name"] == "Project Squad")
    assert squad["projects_count"] == 2
