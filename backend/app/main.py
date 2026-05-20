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
        await conn.run_sync(Base.metadata.create_all)
        if engine.dialect.name == "postgresql":
            await conn.execute(text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'platform_admin'"))
            await conn.execute(text("ALTER TYPE subscriptionplan ADD VALUE IF NOT EXISTS 'starter'"))
            await conn.execute(text("ALTER TYPE subscriptionplan ADD VALUE IF NOT EXISTS 'scale'"))
            await conn.execute(text("ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'WAITING_VERIFY'"))
            await conn.execute(text("ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'REJECTED'"))
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

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
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
