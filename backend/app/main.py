"""NhaTro Manager - FastAPI Main Application"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging
from sqlalchemy import text

from app.core.config import settings
from app.api.v1.router import api_router
from app.models.models import Base
from app.database.session import engine
from app.core.redis_client import RedisClient
from app.services.redis_service import RedisService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting NhaTro Manager API...")
    
    # Initialize Redis Client Singleton
    RedisClient.initialize()
    await RedisClient.check_health()
    
    async with engine.begin() as conn:
        # Create enum types & add missing values in a single DO $$ block
        # to avoid pgbouncer prepared statement cache conflicts
        if engine.dialect.name == "postgresql":
            await conn.execute(text("""
                DO $$ BEGIN
                    -- Create new enum types if not exist
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'proofstatus') THEN
                        CREATE TYPE proofstatus AS ENUM ('pending', 'verified', 'rejected');
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'repairstatus') THEN
                        CREATE TYPE repairstatus AS ENUM ('pending', 'processing', 'completed', 'rejected');
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'complaintstatus') THEN
                        CREATE TYPE complaintstatus AS ENUM ('pending', 'processing', 'completed');
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'terminationtype') THEN
                        CREATE TYPE terminationtype AS ENUM (
                            'TENANT_EARLY_TERMINATION',
                            'ABANDONED_ROOM',
                            'CONTRACT_EXPIRED',
                            'LANDLORD_TERMINATION',
                            'FORCE_MAJEURE',
                            'DEPOSIT_FORFEITURE'
                        );
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'debtstatus') THEN
                        CREATE TYPE debtstatus AS ENUM ('OPEN', 'SETTLED', 'WRITTEN_OFF');
                    END IF;
                    -- Add missing values to existing enums
                    BEGIN ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'platform_admin'; EXCEPTION WHEN duplicate_object THEN NULL; END;
                    BEGIN ALTER TYPE subscriptionplan ADD VALUE IF NOT EXISTS 'starter'; EXCEPTION WHEN duplicate_object THEN NULL; END;
                    BEGIN ALTER TYPE subscriptionplan ADD VALUE IF NOT EXISTS 'scale'; EXCEPTION WHEN duplicate_object THEN NULL; END;
                    BEGIN ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'WAITING_VERIFY'; EXCEPTION WHEN duplicate_object THEN NULL; END;
                    BEGIN ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'REJECTED'; EXCEPTION WHEN duplicate_object THEN NULL; END;
                    BEGIN ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'UNPAID'; EXCEPTION WHEN duplicate_object THEN NULL; END;
                    BEGIN ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'PARTIAL'; EXCEPTION WHEN duplicate_object THEN NULL; END;
                    BEGIN ALTER TYPE contractstatus ADD VALUE IF NOT EXISTS 'PAYMENT_OVERDUE'; EXCEPTION WHEN duplicate_object THEN NULL; END;
                    BEGIN ALTER TYPE contractstatus ADD VALUE IF NOT EXISTS 'NO_RESPONSE'; EXCEPTION WHEN duplicate_object THEN NULL; END;
                    BEGIN ALTER TYPE contractstatus ADD VALUE IF NOT EXISTS 'ABANDONED_ROOM'; EXCEPTION WHEN duplicate_object THEN NULL; END;
                    BEGIN ALTER TYPE terminationtype ADD VALUE IF NOT EXISTS 'DEPOSIT_FORFEITURE'; EXCEPTION WHEN duplicate_object THEN NULL; END;
                END $$;
            """))
        try:
            await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            logger.warning(f"Error during create_all: {e}")
    logger.info("Database tables created/verified")
    yield
    
    # Shutdown
    await engine.dispose()
    # Close Redis connections
    await RedisClient.close()
    logger.info("Application shut down")


app = FastAPI(
    title="NhaTro Manager API",
    description="Multi-tenant SaaS platform for boarding house management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── Middleware ───────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Production Redis-based Rate Limiter Middleware"""
    client_ip = request.client.host if request.client else "unknown_ip"
    path = request.url.path
    
    # Exclude Swagger/static assets and health check from rate limiting
    if path in ("/health", "/", "/docs", "/openapi.json") or path.startswith("/uploads"):
        return await call_next(request)
        
    # Configure custom rate limit rules
    limit = 100  # Default: 100 requests per minute
    window = 60  # Default window: 60 seconds
    
    # Stricter rules for sensitive/authentication endpoints
    if "/auth" in path or "/login" in path:
        limit = 15  # 15 requests per minute
        
    rate_key = f"rate_limit:{client_ip}:{path}"
    
    # Perform rate limit check using RedisService
    allowed = await RedisService.rate_limit(rate_key, limit, window)
    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Quá nhiều yêu cầu. Vui lòng thử lại sau."},
        )
        
    return await call_next(request)


# ─── Exception Handlers ──────────────────────────────────

from fastapi.exceptions import RequestValidationError

def _get_cors_headers(request: Request) -> dict:
    origin = request.headers.get("origin")
    if not origin:
        return {}
    allowed_origins = settings.cors_origins_list
    if "*" in allowed_origins or origin in allowed_origins:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    return {}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Convert errors to JSON-serializable dict using fastapi encoder
    from fastapi.encoders import jsonable_encoder
    errors_data = jsonable_encoder(exc.errors())
    try:
        with open("d:\\nhatro\\backend\\error_log.txt", "a", encoding="utf-8") as f:
            f.write(f"\n=== VALIDATION ERROR AT {request.method} {request.url.path} ===\n")
            f.write(str(errors_data))
            f.write("\n==============================================\n")
    except Exception:
        pass
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors_data},
        headers=_get_cors_headers(request),
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    import traceback
    try:
        with open("d:\\nhatro\\backend\\error_log.txt", "a", encoding="utf-8") as f:
            f.write(f"\n=== GLOBAL EXCEPTION HANDLER AT {request.method} {request.url.path} ===\n")
            f.write(traceback.format_exc())
            f.write("==============================================\n")
    except Exception as log_err:
        logger.error(f"Failed to write to error_log.txt: {log_err}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"},
        headers=_get_cors_headers(request),
    )



# ─── Routes ──────────────────────────────────────────────

app.include_router(api_router, prefix="/api/v1")

from fastapi.staticfiles import StaticFiles
import os

# Ensure uploads directory exists
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
