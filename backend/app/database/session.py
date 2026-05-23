from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import ssl

def _database_url_and_connect_args() -> tuple[str, dict]:
    parsed = urlsplit(settings.DATABASE_URL)
    scheme = parsed.scheme
    if scheme == "postgresql":
        scheme = "postgresql+asyncpg"

    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    ssl_mode = query.pop("sslmode", settings.DATABASE_SSL_MODE)
    query.pop("pgbouncer", None)

    connect_args = {}
    if ssl_mode and ssl_mode.lower() not in {"disable", "false", "0"}:
        # Tạo cấu hình SSL cho phép bỏ qua xác thực chứng chỉ self-signed công cộng
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connect_args["ssl"] = ssl_context
    if settings.DATABASE_DISABLE_PREPARED_STATEMENT_CACHE:
        connect_args["prepared_statement_cache_size"] = 0
        connect_args["statement_cache_size"] = 0

    database_url = urlunsplit(
        (
            scheme,
            parsed.netloc,
            parsed.path,
            urlencode(query),
            parsed.fragment,
        )
    )
    return database_url, connect_args


database_url, connect_args = _database_url_and_connect_args()
engine_kwargs = {
    "echo": settings.DEBUG,
    "pool_pre_ping": True,
    "connect_args": connect_args,
}
if settings.DATABASE_USE_NULL_POOL:
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW

engine = create_async_engine(database_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
