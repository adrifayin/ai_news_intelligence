"""
Database Manager with Connection Pooling and Retry Logic
Improved database layer with better error handling and monitoring
"""

import time
from contextlib import contextmanager
from typing import Optional, Callable
from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError, IntegrityError

from backend.config import config
from backend.exceptions import DatabaseException
from backend.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Manages database connections with pooling and retry logic."""

    def __init__(self):
        self._engine = None
        self._session_factory = None
        self._initialized = False

    def initialize(self):
        """Initialize database engine with connection pooling."""
        if self._initialized:
            logger.warning("Database already initialized")
            return

        logger.info("Initializing database connection pool...")

        # Connection pool configuration
        if config.DATABASE_URL.startswith("sqlite"):
            # SQLite-specific settings
            self._engine = create_engine(
                config.DATABASE_URL,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 30,
                },
                pool_pre_ping=True,  # Verify connections before using
                echo=config.DEBUG,
            )

            # Enable WAL mode for better concurrency
            @event.listens_for(self._engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
                cursor.close()

        else:
            # PostgreSQL/MySQL settings
            self._engine = create_engine(
                config.DATABASE_URL,
                pool_size=config.DB_POOL_SIZE,
                max_overflow=config.DB_MAX_OVERFLOW,
                pool_timeout=config.DB_POOL_TIMEOUT,
                pool_recycle=config.DB_POOL_RECYCLE,
                pool_pre_ping=True,
                echo=config.DEBUG,
            )

        self._session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine
        )

        self._initialized = True
        logger.info(f"✓ Database initialized: {config.DATABASE_URL.split('://')[0]}://...")

    @property
    def engine(self):
        """Get database engine."""
        if not self._initialized:
            self.initialize()
        return self._engine

    @property
    def session_factory(self):
        """Get session factory."""
        if not self._initialized:
            self.initialize()
        return self._session_factory

    @contextmanager
    def get_session(self) -> Session:
        """
        Get a database session with automatic cleanup.

        Usage:
            with db_manager.get_session() as session:
                session.query(Article).all()
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise DatabaseException(f"Database operation failed: {str(e)}")
        finally:
            session.close()

    def execute_with_retry(
        self,
        operation: Callable,
        max_retries: int = 3,
        backoff_factor: float = 2.0
    ):
        """
        Execute a database operation with retry logic.

        Args:
            operation: Function to execute
            max_retries: Maximum number of retry attempts
            backoff_factor: Exponential backoff multiplier
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                return operation()
            except OperationalError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    logger.warning(
                        f"Database operation failed (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {wait_time}s... Error: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Database operation failed after {max_retries} attempts")
            except IntegrityError as e:
                # Don't retry integrity errors (unique constraint violations, etc.)
                logger.debug(f"Integrity error (expected for duplicates): {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected database error: {e}")
                raise

        raise DatabaseException(f"Operation failed after {max_retries} retries: {last_exception}")

    def health_check(self) -> dict:
        """Check database health and connection pool status."""
        try:
            from sqlalchemy import text
            with self.get_session() as session:
                session.execute(text("SELECT 1"))

            pool_status = self._engine.pool.status() if hasattr(self._engine.pool, 'status') else "N/A"

            return {
                "status": "healthy",
                "pool_status": pool_status,
                "database_type": config.DATABASE_URL.split("://")[0],
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def get_pool_stats(self) -> dict:
        """Get connection pool statistics."""
        if not self._initialized:
            return {"status": "not_initialized"}

        pool = self._engine.pool
        return {
            "size": pool.size() if hasattr(pool, 'size') else "N/A",
            "checked_in": pool.checkedin() if hasattr(pool, 'checkedin') else "N/A",
            "checked_out": pool.checkedout() if hasattr(pool, 'checkedout') else "N/A",
            "overflow": pool.overflow() if hasattr(pool, 'overflow') else "N/A",
        }

    def close(self):
        """Close database connections."""
        if self._initialized and self._engine:
            logger.info("Closing database connections...")
            self._engine.dispose()
            self._initialized = False
            logger.info("✓ Database connections closed")


# Global singleton
db_manager = DatabaseManager()
