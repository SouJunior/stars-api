import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import models, schemas
import time

# Configuração do banco de dados de teste em memória
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_volunteers_order.db"
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

def test_volunteers_order_default_desc():
    db = TestingSessionLocal()
    job_title = models.JobTitle(title="Developer", is_active=True)
    db.add(job_title)
    db.commit()
    db.refresh(job_title)
    
    # Create volunteers with slight delay to ensure different timestamps
    volunteers = []
    for i in range(3):
        volunteer = models.Volunteer(
            name=f"Volunteer {i}",
            email=f"volunteer{i}@example.com",
            linkedin=f"https://linkedin.com/in/volunteer{i}",
            jobtitle_id=job_title.id,
            is_active=True
        )
        db.add(volunteer)
        db.commit()
        db.refresh(volunteer)
        volunteers.append(volunteer)
        time.sleep(0.1) # Ensure created_at differs slightly if precision allows
    
    db.close()

    # Default order (should be desc)
    response = client.get("/volunteers/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["name"] == "Volunteer 2"
    assert data[1]["name"] == "Volunteer 1"
    assert data[2]["name"] == "Volunteer 0"

def test_volunteers_order_asc():
    db = TestingSessionLocal()
    job_title = models.JobTitle(title="Developer", is_active=True)
    db.add(job_title)
    db.commit()
    db.refresh(job_title)
    
    # Create volunteers
    volunteers = []
    for i in range(3):
        volunteer = models.Volunteer(
            name=f"Volunteer {i}",
            email=f"volunteer{i}@example.com",
            linkedin=f"https://linkedin.com/in/volunteer{i}",
            jobtitle_id=job_title.id,
            is_active=True
        )
        db.add(volunteer)
        db.commit()
        time.sleep(0.1)
    
    db.close()

    # Order ASC
    response = client.get("/volunteers/?order=asc")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["name"] == "Volunteer 0"
    assert data[1]["name"] == "Volunteer 1"
    assert data[2]["name"] == "Volunteer 2"
