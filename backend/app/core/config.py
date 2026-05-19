from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import secrets
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # App
    APP_NAME: str = "NhaTro Manager"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = ""
    DATABASE_SSL_MODE: str = "disable"
    DATABASE_USE_NULL_POOL: bool = False
    DATABASE_DISABLE_PREPARED_STATEMENT_CACHE: bool = True
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    @field_validator("DATABASE_URL")
    @classmethod
    def database_url_required(cls, value: str) -> str:
        if not value:
            raise ValueError(
                "DATABASE_URL is required. Set it as an environment variable on Railway."
            )
        return value

    # JWT
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    FRONTEND_URL: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@nhatro.vn"
    RESEND_API_KEY: str = ""

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # PayOS
    PAYOS_CLIENT_ID: str = ""
    PAYOS_API_KEY: str = ""
    PAYOS_CHECKSUM_KEY: str = ""
    PAYOS_RETURN_URL: str = "http://localhost:3000/payment/success"
    PAYOS_CANCEL_URL: str = "http://localhost:3000/payment/cancel"

    # VietQR
    VIETQR_BASE_URL: str = "https://img.vietqr.io/image"

    # Subscription limits
    FREE_PLAN_MAX_ROOMS: int = 10
    BASIC_PLAN_MAX_ROOMS: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


import os
import logging

_logger = logging.getLogger(__name__)

# Railway may provide DB URL under different names - map them to DATABASE_URL
_RAILWAY_DB_ALIASES = [
    "DATABASE_URL",
    "DATABASE_PRIVATE_URL",
    "DATABASE_PUBLIC_URL",
    "RAILWAY_DATABASE_URL",
]

if not os.environ.get("DATABASE_URL"):
    for alias in _RAILWAY_DB_ALIASES[1:]:
        val = os.environ.get(alias)
        if val:
            os.environ["DATABASE_URL"] = val
            _logger.info(f"Mapped {alias} → DATABASE_URL")
            break

# Debug: log available env vars at startup (redacted)
_db_url = os.environ.get("DATABASE_URL", "")
_logger.info(f"DATABASE_URL present: {bool(_db_url)}, length: {len(_db_url)}")

settings = Settings()
