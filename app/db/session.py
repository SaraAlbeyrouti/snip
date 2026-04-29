from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Single engine instance per process. pool_pre_ping avoids stale connection errors.
engine = create_async_engine(settings.database_url, pool_pre_ping=True)

# Session factory. expire_on_commit=False so we can read attributes after commit.
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yield a database session, close it after the request."""
    async with SessionLocal() as session:
        yield session
