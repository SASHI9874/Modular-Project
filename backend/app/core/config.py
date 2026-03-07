import os
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Builder Platform"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_this_secret_key_in_production")
    
    # Database
    # POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    # POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    # POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    # POSTGRES_DB: str = os.getenv("POSTGRES_DB", "ai_builder")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "databse_url")
    
    # MinIO
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ROOT_USER", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
    MINIO_BUCKET_NAME: str = "feature-store"
    MINIO_SECURE: bool = False

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return self.DATABASE_URL


    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()