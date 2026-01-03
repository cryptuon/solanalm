"""
Async Database Connection Management for SolanaLM

Provides SQLAlchemy async engine, session factory, and connection pooling.
"""

import logging
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

from core.config.settings import get_settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages async database connections with proper pooling.

    Usage:
        db = DatabaseManager()
        await db.initialize()

        async with db.session() as session:
            # Use session for queries
            pass

        await db.close()
    """

    _instance: Optional["DatabaseManager"] = None

    def __init__(self):
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def initialize(self, database_url: Optional[str] = None) -> None:
        """Initialize database engine and session factory"""
        if self._initialized:
            logger.debug("Database already initialized")
            return

        settings = get_settings()
        url = database_url or settings.database_url

        # Convert postgresql:// to postgresql+asyncpg://
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("sqlite://"):
            url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)

        # Determine pool settings based on environment
        is_development = settings.environment.value == "development"

        if "sqlite" in url:
            # SQLite doesn't support connection pooling
            self.engine = create_async_engine(
                url,
                echo=is_development,
                poolclass=NullPool
            )
        else:
            # PostgreSQL with connection pooling
            self.engine = create_async_engine(
                url,
                poolclass=AsyncAdaptedQueuePool,
                pool_size=20,           # Base connections
                max_overflow=30,        # Additional connections under load
                pool_timeout=30,        # Wait time for connection
                pool_recycle=1800,      # Recycle connections every 30 min
                pool_pre_ping=True,     # Verify connections before use
                echo=is_development
            )

        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )

        self._initialized = True
        logger.info(f"Database initialized with URL: {url[:30]}...")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session with automatic commit/rollback"""
        if not self._initialized or not self.session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def close(self) -> None:
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("Database connections closed")

    async def health_check(self) -> bool:
        """Check database connectivity"""
        if not self._initialized:
            return False

        try:
            async with self.session() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


async def init_database(database_url: Optional[str] = None) -> DatabaseManager:
    """Initialize global database manager"""
    global _db_manager
    _db_manager = DatabaseManager.get_instance()
    await _db_manager.initialize(database_url)
    return _db_manager


async def close_database() -> None:
    """Close global database manager"""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.

    Usage:
        @app.get("/users")
        async def get_users(session: AsyncSession = Depends(get_db_session)):
            # Use session
            pass
    """
    if not _db_manager:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    async with _db_manager.session() as session:
        yield session


def get_database_manager() -> DatabaseManager:
    """Get global database manager instance"""
    if not _db_manager:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db_manager
