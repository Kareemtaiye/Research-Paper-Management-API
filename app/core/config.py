import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine which env file to use BEFORE loading the class
# Default to '.env' if no ENV variable is explicitly set in the terminal
ENV_FILE = ".env.test" if os.getenv("ENV") == "test" else ".env"


class Settings(BaseSettings):
    # Let Pydantic automatically fetch these from the environment/env_file
    database_url: str
    prod_database_url: str
    secret_key: str
    env: str = "development"

    redis_cache_url: Optional[str] = None
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None
    redis_pubsub_url: Optional[str] = None

    prod_redis_cache_url: str
    prod_celery_broker_url: str
    prod_celery_result_backend: str
    prod_redis_pubsub_url: str
    es_url: str
    prod_es_url: str

    # Email
    resend_api_key: str
    from_email: str
    mail_hog_smtp_host: str
    mail_hog_smtp_port: int
    mail_hog_from_email: str
    noreply_email: str
    from_email_test: str
    reply_to_email: str
    display_name: str

    # Pydantic will automatically cast these strings from the env to integers
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # 3. Tell Pydantic which file to read
    # ---- v2 -----
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        # CRITICAL: Prevents crashes if the file is missing in a Docker/Prod environment
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.env.lower() in ("production", "prod")

    # ----- v1 -------
    # class Config:
    #     env_file = ".env"
    #     test_env_file = ".env.test"


settings = Settings()
