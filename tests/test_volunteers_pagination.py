import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import models, schemas

# Configuração do banco de dados de teste em memória
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_volunteers.db"
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

@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_volunteers_pagination():
    db = TestingSessionLocal()
    # Create a job title first (required for volunteer)
    job_title = models.JobTitle(title="Developer", is_active=True)
    db.add(job_title)
    db.commit()
    db.refresh(job_title)
    
    # Create 15 volunteers
    for i in range(15):
        volunteer = models.Volunteer(
            name=f"Volunteer {i}",
            email=f"volunteer{i}@example.com",
            linkedin=f"https://linkedin.com/in/volunteer{i}",
            jobtitle_id=job_title.id,
            is_active=True
        )
        db.add(volunteer)
    db.commit()
    db.close()

    # Test Page 1: Limit 5, Skip 0
    response = client.get("/volunteers/?skip=0&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert data[0]["name"] == "Volunteer 0"
    assert data[4]["name"] == "Volunteer 4"

    # Test Page 2: Limit 5, Skip 5
    response = client.get("/volunteers/?skip=5&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert data[0]["name"] == "Volunteer 5"
    assert data[4]["name"] == "Volunteer 9"

    # Test Page 3: Limit 5, Skip 10
    response = client.get("/volunteers/?skip=10&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert data[0]["name"] == "Volunteer 10"
    assert data[4]["name"] == "Volunteer 14"

    # Test Page 4: Limit 5, Skip 15 (Should be empty)
    response = client.get("/volunteers/?skip=15&limit=5")
    assert response.status_code == 200 # Or whatever status code empty list returns, usually 200 with []
    data = response.json()
    assert len(data) == 0
