import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from .settings import Settings

load_dotenv()
settings = Settings()

#SQLALCHEMY_DATABASE_URL = f"{os.getenv('DB_DRIVER')}://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_DATABASE')}"

SQLALCHEMY_DATABASE_URL = (
    f"{settings.DB_DRIVER}://{settings.DB_USERNAME}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_DATABASE}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
metadata = Base.metadata
