import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine which env file to use BEFORE loading the class
# Default to '.env' if no ENV variable is explicitly set in the terminal
ENV_FILE = ".env.test" if os.getenv("ENV") == "test" else ".env"

class Settings(BaseSettings):
    # Let Pydantic automatically fetch these from the environment/env_file
    database_url: str 
    secret_key: str 
    env: str = "development"
    redis_url: str 

    # Pydantic will automatically cast these strings from the env to integers
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int =  7

    # 3. Tell Pydantic which file to read
    # ---- v2 -----
    model_config = SettingsConfigDict(
        env_file = ENV_FILE,
        extra = "ignore"
    )

    # ----- v1 -------
    # class Config:
    #     env_file = ".env"
    #     test_env_file = ".env.test"
    


settings = Settings()