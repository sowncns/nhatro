from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import List
import secrets
from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # App
    APP_NAME: str = "NhaTro Manager"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
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
                "DATABASE_URL is required. Use your Supabase PostgreSQL connection string."
            )
        return value

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # CORS
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    # Email
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@nhatro.vn")
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")

    # Stripe
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # PayOS
    PAYOS_CLIENT_ID: str = os.getenv("PAYOS_CLIENT_ID", "")
    PAYOS_API_KEY: str = os.getenv("PAYOS_API_KEY", "")
    PAYOS_CHECKSUM_KEY: str = os.getenv("PAYOS_CHECKSUM_KEY", "")
    PAYOS_RETURN_URL: str = os.getenv("PAYOS_RETURN_URL", "http://localhost:3000/payment/success")
    PAYOS_CANCEL_URL: str = os.getenv("PAYOS_CANCEL_URL", "http://localhost:3000/payment/cancel")

    # VietQR
    VIETQR_BASE_URL: str = os.getenv("VIETQR_BASE_URL", "https://img.vietqr.io/image")

    # Subscription limits
    FREE_PLAN_MAX_ROOMS: int = 10
    BASIC_PLAN_MAX_ROOMS: int = 50

    class Config:
        env_file = BACKEND_DIR / ".env"
        case_sensitive = True


settings = Settings()
