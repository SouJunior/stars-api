from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_DRIVER: str
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_DATABASE: str

    class config:
        env_prexix = 'DB_'

settings = Settings()