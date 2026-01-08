"""
Database Connection Management

SQLAlchemy engine and session configuration.
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from api.config import settings
from api.database.models import Base, User

logger = logging.getLogger(__name__)


# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20,
)


# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database by creating all tables and default user.

    This should be called during application startup.
    """
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        # Create default user if it doesn't exist
        create_default_user()

    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def create_default_user():
    """
    Create a default user for session management.

    This ensures that the foreign key constraint for sessions
    can be satisfied when creating sessions without explicit user management.
    """
    db = SessionLocal()
    try:
        # Check if default user already exists
        from sqlalchemy import select

        stmt = select(User).where(User.username == "default_user")
        result = db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.info("Default user already exists")
            return

        # Create default user
        default_user = User(
            user_id="default_user",
            username="default_user",
            email="default@apgi-system.local",
            password_hash="no_password_required",  # Not used for API access
            roles=["user", "session_manager"],
        )

        db.add(default_user)
        db.commit()
        logger.info("Default user created successfully")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create default user: {e}")
        raise
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.

    Yields:
        Session: SQLAlchemy database session

    Usage:
        @app.get("/endpoint")
        async def endpoint(db: Session = Depends(get_db)):
            # Use db session
            pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database session.

    Yields:
        Session: SQLAlchemy database session

    Usage:
        with get_db_context() as db:
            # Use db session
            pass
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def close_db():
    """
    Close database connections.

    This should be called during application shutdown.
    """
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
