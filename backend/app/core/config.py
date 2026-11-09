import os
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "MediAssist AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = "mediassist-super-secret-production-grade-key-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    # Database
    # Supports both PostgreSQL (asyncpg) and SQLite (aiosqlite)
    DATABASE_URL: str = "sqlite+aiosqlite:///./mediassist.db"
    
    # Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ]

    class Config:
        case_sensitive = True
        env_file = (".env", "backend/.env")
        extra = "allow"

settings = Settings()

