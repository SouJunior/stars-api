import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Override DATABASE_URL before any app imports so database.py uses SQLite, not MySQL
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

# Provide defaults so settings load without a real .env
os.environ.setdefault("DB_DRIVER", "mysql+mysqlconnector")
os.environ.setdefault("DB_USERNAME", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "3306")
os.environ.setdefault("DB_DATABASE", "test")
os.environ.setdefault("JWT_SECRETE_KEY", "test-secret-key-for-tests-only")
os.environ.setdefault("PASSWORD_HASH_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "30")
os.environ.setdefault("BREVO_API_KEY", "test-brevo-key")
os.environ.setdefault("REGISTRATION_CODE", "changeme")

# Patch app.database engine BEFORE app.main is imported so
# the module-level create_all in main.py targets SQLite, not MySQL.
import app.database as _db_module  # noqa: E402

_bootstrap_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_bootstrap_session = sessionmaker(autocommit=False, autoflush=False, bind=_bootstrap_engine)

_db_module.engine = _bootstrap_engine
_db_module.SessionLocal = _bootstrap_session

from app.main import app  # noqa: E402
from app.database import get_db  # noqa: E402
from app.models import Base, VolunteerStatus  # noqa: E402


@pytest.fixture(scope="function")
def db():
    """
    Isolated SQLite in-memory database per test.
    Yields a session for seeding data; overrides the app get_db dependency
    so the test client uses the same underlying connection.
    Bootstraps required lookup data (VolunteerStatus) so volunteer creation works.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    seed_session = SessionLocal()

    # Required by create_volunteer in crud.py
    seed_session.add(VolunteerStatus(name="INTERESTED", description="Voluntário interessado"))
    seed_session.commit()

    def override_get_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield seed_session

    seed_session.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    with TestClient(app) as c:
        yield c
