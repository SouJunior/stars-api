from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import os

load_dotenv()
class __Settings(BaseSettings):
    DB_DRIVER: str 
    DB_USERNAME: str 
    DB_PASSWORD: str 
    DB_HOST: str
    DB_PORT: int 
    DB_DATABASE: str 

def get_settings():
    return __Settings()

settings =  get_settings()   