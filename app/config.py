import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    """
    Konfigurasi aplikasi, dibaca dari environment variables.
    """
    
    # Konfigurasi Database (diubah untuk SQLite)
    # Format: "sqlite+aiosqlite:///./nama_file_database.db"
    DATABASE_URL: str

    # Konfigurasi JWT (Authentication) - TIDAK BERUBAH
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 1 hari

    # Konfigurasi Middleware - TIDAK BERUBAH
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    ALLOWED_HOSTS: List[str] = ["*"]

    # Menentukan file .env yang akan dibaca
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

# Buat satu instance settings yang akan di-import ke file lain
settings = Settings()