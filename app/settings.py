from pydantic_settings import BaseSettings, SettingsConfigDict

class __Settings(BaseSettings):
    DB_DRIVER: str
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_DATABASE: str
    JWT_SECRETE_KEY: str
    PASSWORD_HASH_ALGORITHM: str
    JWT_EXPIRE_MINUTES: int
    BREVO_API_KEY: str

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

settings = __Settings() # type:ignore