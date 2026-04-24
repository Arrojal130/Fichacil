"""
FichaFacil MVP - Configuration
Loads settings from environment variables.
"""
from functools import lru_cache
from typing import ClassVar

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    DEBUG_LAN_ORIGIN_REGEX: ClassVar[str] = (
        r"http://(?:192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|"
        r"172\.(?:1[6-9]|2\d|3[0-1])\.\d+\.\d+):3000"
    )
    LOCAL_DEV_SECRET_KEY: ClassVar[str] = "local-dev-only-secret-key-not-for-production"
    INSECURE_SECRET_KEY_MARKERS: ClassVar[tuple[str, ...]] = (
        "change-in-production",
        "your-secret",
        "replace-me",
        "changeme",
        "example",
    )
    MIN_PRODUCTION_SECRET_KEY_LENGTH: ClassVar[int] = 32

    # Database
    database_url: str = "sqlite+aiosqlite:///./fichafacil.db"

    # JWT
    secret_key: str | None = None
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # App
    app_name: str = "FichaFacil"
    debug: bool = False
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000,http://localhost:5500,http://127.0.0.1:5500"
    cors_origins: str | None = None  # Preferred override for allowed_origins from .env

    # Geolocation
    max_distance_meters: int = 500

    # Rate limiting
    rate_limit_per_minute: int = 10

    @model_validator(mode="after")
    def validate_secret_key_for_runtime(self) -> "Settings":
        """Require an explicit secure SECRET_KEY outside local debug mode."""
        secret = (self.secret_key or "").strip()

        if self.debug:
            if not secret:
                self.secret_key = self.LOCAL_DEV_SECRET_KEY
            return self

        if not secret:
            raise ValueError("SECRET_KEY es obligatorio cuando DEBUG=false")

        lowered_secret = secret.lower()
        if (
            len(secret) < self.MIN_PRODUCTION_SECRET_KEY_LENGTH
            or any(marker in lowered_secret for marker in self.INSECURE_SECRET_KEY_MARKERS)
        ):
            raise ValueError(
                "SECRET_KEY inseguro para producción: usa un valor aleatorio de al menos 32 caracteres"
            )

        self.secret_key = secret
        return self

    @property
    def effective_allowed_origins(self) -> list[str]:
        """Return normalized CORS origins, preferring the explicit alias when present."""
        raw_origins = self.cors_origins if self.cors_origins is not None else self.allowed_origins
        return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

    @property
    def cors_origin_regex(self) -> str | None:
        """Allow local LAN development origins only when debug mode is enabled."""
        if not self.debug:
            return None
        return self.DEBUG_LAN_ORIGIN_REGEX

@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
