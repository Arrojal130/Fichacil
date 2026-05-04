"""
FichaFacil MVP - Database Setup
SQLAlchemy async configuration with SQLite/PostgreSQL support.
"""
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings
from app.migrations import apply_migrations

settings = get_settings()


def normalize_database_url(database_url: str) -> str:
    """Normalize provider database URLs for SQLAlchemy async drivers."""
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return database_url


database_url = normalize_database_url(settings.database_url)

# Ensure data directory exists for SQLite
if "sqlite" in database_url:
    db_path = database_url.split("///")[-1]
    db_dir = Path(db_path).parent
    if db_dir and str(db_dir) != ".":
        db_dir.mkdir(parents=True, exist_ok=True)

# Create async engine
# SQLite WAL mode for better concurrency
engine = create_async_engine(
    database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


async def get_db():
    """Dependency to get database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database schema by applying versioned migrations."""
    async with engine.begin() as conn:
        await apply_migrations(conn)


async def close_db():
    """Close database connection."""
    await engine.dispose()
