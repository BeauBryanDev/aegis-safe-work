
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
 
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
 
from app.core.config import settings
 

# Engine
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,        # validate connections before checkout
    echo=settings.DB_ECHO,
)
 

# Session factory
 
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,    # avoid lazy-load issues after commit in async context
    autocommit=False,
    autoflush=False,
)
 

# Declarative base — all ORM models inherit from this
 
class Base(DeclarativeBase):
    pass
 
# Dependency — FastAPI router injection via get_db()
 
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency. Yields an AsyncSession and guarantees cleanup.
 
    Usage in router:
        @router.get("/alerts")
        async def get_alerts(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
 
# Context manager — service layer usage outside FastAPI dependency injection
 
@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for use in services or background tasks
    that run outside the FastAPI request/response cycle.
 
    Usage:
        async with get_db_context() as session:
            await session.execute(...)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
 
# Table creation helper — called from main.py lifespan on startup

async def create_tables() -> None:
    """
    Create all tables defined in ORM models if they do not exist.
    Called once on application startup via lifespan context manager.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
 

# Teardown helper — called from main.py lifespan on shutdown
 
async def close_engine() -> None:
    """
    Dispose the connection pool on application shutdown.
    Called from lifespan context manager.
    """
    await engine.dispose()