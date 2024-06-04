from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_DRIVER: str = 'mysql+mysqlconnector'
    DB_USERNAME: str = 'mysql'
    DB_PASSWORD: str = 'mysql'
    DB_HOST: str = 'mysql_database'
    DB_PORT: int = 3306
    DB_DATABASE: str = 'db'

    class config:
        env_prefix = 'DB_'