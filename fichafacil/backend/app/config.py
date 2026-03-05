"""
FichaFacil MVP - Configuration
Loads settings from environment variables.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./fichafacil.db"
    
    # JWT
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    # App
    app_name: str = "FichaFacil"
    debug: bool = True
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000,http://localhost:5500,http://127.0.0.1:5500,http://192.168.1.42:3000"
    cors_origins: str = ""  # Alias for allowed_origins from .env
    
    # Geolocation
    max_distance_meters: int = 500
    
    # Rate limiting
    rate_limit_per_minute: int = 10
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
