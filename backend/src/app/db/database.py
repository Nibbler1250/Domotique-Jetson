"""Database connection and session management using SQLAlchemy Core."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from app.core.config import get_settings

# Naming convention for constraints (Alembic compatibility)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)

# Engine singleton
_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,
        )
    return _engine


async def dispose_engine() -> None:
    """Dispose the database engine."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


@asynccontextmanager
async def get_connection() -> AsyncGenerator[AsyncConnection, None]:
    """Get a database connection from the pool."""
    engine = get_engine()
    async with engine.connect() as conn:
        yield conn


async def init_db() -> None:
    """Initialize database tables."""
    # Import models to register them with metadata
    from app.models import automations  # noqa: F401
    from app.models import devices  # noqa: F401
    from app.models import modes  # noqa: F401
    from app.models import permissions  # noqa: F401
    from app.models import profiles  # noqa: F401
    from app.models import users  # noqa: F401

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
