import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.settings import settings

# Configuração do banco de dados de teste em memória
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_reg.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Cria as tabelas no banco de dados de teste
Base.metadata.create_all(bind=engine)

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
    # Limpa e recria as tabelas antes de todos os testes no módulo
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Limpa as tabelas depois que todos os testes no módulo forem executados
    Base.metadata.drop_all(bind=engine)

def test_create_user_invalid_code():
    response = client.post(
        "/users/",
        json={"email": "invalid_code@example.com", "password": "testpassword", "registration_code": "wrongcode"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid registration code"}

def test_create_user_valid_code():
    # Using the default "changeme" which is set in settings.py if not in env
    # If env overrides it, this test might fail if we don't know the env value. 
    # But we set the default in the code earlier.
    
    current_code = settings.REGISTRATION_CODE
    
    response = client.post(
        "/users/",
        json={"email": "valid_code@example.com", "password": "testpassword", "registration_code": current_code},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "valid_code@example.com"
