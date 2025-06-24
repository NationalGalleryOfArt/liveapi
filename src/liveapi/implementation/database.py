"""Database connection and session management for SQLModel."""

import os
from typing import Generator, Optional
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.engine import Engine


class DatabaseManager:
    """Manages database connections and sessions for SQLModel."""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager.

        Args:
            database_url: Database connection URL. If None, uses DATABASE_URL env var
                         or defaults to SQLite in-memory database for development.
        """
        self.database_url = database_url or self._get_database_url()
        self.engine: Optional[Engine] = None
        self._initialized = False

    def _get_database_url(self) -> str:
        """Get database URL from environment or return default."""
        # Check environment variable first
        if "DATABASE_URL" in os.environ:
            return os.environ["DATABASE_URL"]

        # Default to SQLite for development/testing
        return "sqlite:///./liveapi.db"

    def get_engine(self) -> Engine:
        """Get or create database engine."""
        if self.engine is None:
            # Configure engine based on database type
            if self.database_url.startswith("sqlite"):
                # SQLite-specific configuration
                self.engine = create_engine(
                    self.database_url,
                    connect_args={"check_same_thread": False},
                    echo=os.getenv("DATABASE_DEBUG", "false").lower() == "true",
                )
            else:
                # PostgreSQL and other databases
                self.engine = create_engine(
                    self.database_url,
                    echo=os.getenv("DATABASE_DEBUG", "false").lower() == "true",
                )

        return self.engine

    def create_db_and_tables(self) -> None:
        """Create database tables from SQLModel metadata."""
        if not self._initialized:
            engine = self.get_engine()
            SQLModel.metadata.create_all(engine)
            self._initialized = True

    def get_session(self) -> Generator[Session, None, None]:
        """Get database session for dependency injection.

        Yields:
            Database session that is automatically closed after use.
        """
        engine = self.get_engine()
        with Session(engine) as session:
            try:
                yield session
            finally:
                session.close()

    def close(self) -> None:
        """Close database engine and connections."""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self._initialized = False


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get or create global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency for getting database session."""
    db_manager = get_database_manager()
    yield from db_manager.get_session()


def init_database() -> None:
    """Initialize database tables."""
    db_manager = get_database_manager()
    db_manager.create_db_and_tables()


def close_database() -> None:
    """Close database connections."""
    global _db_manager
    if _db_manager:
        _db_manager.close()
        _db_manager = None
