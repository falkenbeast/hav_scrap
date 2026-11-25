import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger("hav_scrap")

# Configure SQLite engine with thread safety support for FastAPI
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

try:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        echo=False,
        future=True
    )
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False
    )
except Exception as e:
    logger.error(f"Failed to create database engine for {settings.DATABASE_URL}: {str(e)}", exc_info=True)
    raise e


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a scoped database session.
    Automatically closes session upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
