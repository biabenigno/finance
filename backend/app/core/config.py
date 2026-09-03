import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://dhwlcympxwynndnmcxwc.supabase.co")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "sb_secret_w3TPLGrTQc5YSHIkhRCZKA_8E-2Jksn")

    class Config:
        env_file = ".env"

settings = Settings()