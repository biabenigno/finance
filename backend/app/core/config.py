import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://dhwlcympxwynndnmcxwc.supabase.co")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "sb_secret_w3TPLGrTQc5YSHIkhRCZKA_8E-2Jksn")
    PLUGGY_CLIENT_ID: str = os.getenv("PLUGGY_CLIENT_ID", "07f0966b-7334-4b85-a94e-f698c09067a4")
    PLUGGY_CLIENT_SECRET: str = os.getenv("PLUGGY_CLIENT_SECRET", "IEMfJhXXwtNtn4ICJvT-e8rwumX1lEVOty0VZ7xCmQU")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()