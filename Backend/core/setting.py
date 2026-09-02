from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    DATABASE_URL_SYNC: str
    SECRET_KEY: str
    REFRESH_TOKEN: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRES: int
    REFRESH_TOKEN_EXPIRES: int



    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str


    class Config:
        case_sensitive = True
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()