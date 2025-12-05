"""
Application configuration management
Supports environment variables and .env files
"""
from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "ForgeData"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    SECRET_KEY: str = "change-this-in-production"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Authentication Integration
    AUTH_API_URL: str = ""
    AUTH_CLIENT_ID: str = ""
    AUTH_CLIENT_SECRET: str = ""
    
    # Database
    DATABASE_URL: str = "sqlite:///./forgedata.db"
    
    # Cloud Providers
    # GCP
    GCP_PROJECT_ID: str = ""
    GCP_CREDENTIALS_PATH: str = ""
    
    # AWS
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    
    # Digital Ocean
    DO_SPACES_KEY: str = ""
    DO_SPACES_SECRET: str = ""
    DO_REGION: str = "nyc3"
    
    # ETL Settings
    ETL_BATCH_SIZE: int = 1000
    ETL_MAX_WORKERS: int = 4
    ANONYMIZATION_ENABLED: bool = True
    DEDUPLICATION_ENABLED: bool = True
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
