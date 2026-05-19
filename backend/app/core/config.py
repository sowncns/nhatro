import os
import secrets
import logging
from typing import List
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env file if it exists (local dev), won't override existing env vars
BACKEND_DIR = Path(__file__).resolve().parents[2]
_env_file = BACKEND_DIR / ".env"
if _env_file.exists():
    load_dotenv(_env_file, override=False)
    logger.info(f"Loaded .env from {_env_file}")

# Railway may provide DB URL under different variable names
for _alias in ["DATABASE_URL", "DATABASE_PRIVATE_URL", "DATABASE_PUBLIC_URL"]:
    if os.environ.get(_alias):
        if _alias != "DATABASE_URL":
            os.environ["DATABASE_URL"] = os.environ[_alias]
            logger.info(f"Mapped {_alias} -> DATABASE_URL")
        break

# Debug startup
_db = os.environ.get("DATABASE_URL", "")
print(f"[config] DATABASE_URL present: {bool(_db)}, len={len(_db)}")
print(f"[config] All env keys with 'DATA': {[k for k in os.environ if 'DATA' in k.upper()]}")


class Settings:
    """Application settings - reads directly from os.environ for maximum compatibility."""

    # App
    APP_NAME: str = "NhaTro Manager"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DATABASE_SSL_MODE: str = os.getenv("DATABASE_SSL_MODE", "disable")
    DATABASE_USE_NULL_POOL: bool = os.getenv("DATABASE_USE_NULL_POOL", "false").lower() in ("true", "1")
    DATABASE_DISABLE_PREPARED_STATEMENT_CACHE: bool = os.getenv("DATABASE_DISABLE_PREPARED_STATEMENT_CACHE", "true").lower() in ("true", "1")
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

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
    FREE_PLAN_MAX_ROOMS: int = int(os.getenv("FREE_PLAN_MAX_ROOMS", "10"))
    BASIC_PLAN_MAX_ROOMS: int = int(os.getenv("BASIC_PLAN_MAX_ROOMS", "50"))


settings = Settings()

if not settings.DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is required! Set it as an environment variable.\n"
        f"Available env vars with 'DATA': {[k for k in os.environ if 'DATA' in k.upper()]}"
    )
