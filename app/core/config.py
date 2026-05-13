import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    database_url: str | None = os.getenv("DATABASE_URL")
    secret_key: str | None = os.getenv("SECRET_KEY")
    access_token_expire_minutes: int = os.getenv("access_token_expire_minutes") or 15
    refresh_token_expire_days: int = os.getenv("refresh_token_expire_days") or 7
    env: str | None = os.getenv("ENV")
    redis_url: str = os.getenv("REDIS_URL")

    class Config:
        env_file = ".env"
        test_env_file = ".env.test"
    


settings = Settings()