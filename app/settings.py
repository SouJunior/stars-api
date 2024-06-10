from pydantic_settings import BaseSettings, SettingsConfigDict

class __Settings(BaseSettings):
    DB_DRIVER: str 
    DB_USERNAME: str 
    DB_PASSWORD: str 
    DB_HOST: str
    DB_PORT: int 
    DB_DATABASE: str 

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

settings = __Settings() # type:ignore