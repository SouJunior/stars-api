import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import User

# Configuração do banco de dados de teste em memória
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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


def test_create_user():
    response = client.post(
        "/users/",
        json={"email": "test@example.com", "password": "testpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "is_active" in data


def test_login_for_access_token():
    # Primeiro, crie um usuário para poder fazer login
    client.post(
        "/users/",
        json={"email": "loginuser@example.com", "password": "loginpassword"},
    )
    
    response = client.post(
        "/token",
        data={"username": "loginuser@example.com", "password": "loginpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_read_users_me_unauthorized():
    response = client.get("/users/me/")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_read_users_me_authorized():
    # Crie um usuário e faça login para obter um token
    client.post(
        "/users/",
        json={"email": "me_user@example.com", "password": "me_password"},
    )
    login_response = client.post(
        "/token",
        data={"username": "me_user@example.com", "password": "me_password"},
    )
    token = login_response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/me/", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me_user@example.com"