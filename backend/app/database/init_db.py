import logging
from app.database.base import Base
from app.database.session import engine
# Import models to ensure they are registered with Base.metadata before create_all
from app.models.company import Company
from app.models.job import JobOpportunity
from app.models.session import ScrapingSession
from app.models.export import ExportHistory
from app.database.migration import migrate_db

logger = logging.getLogger("hav_scrap")


def init_db() -> bool:
    """
    Initializes database schema by generating tables if they do not exist,
    and applies backward-compatible column migrations for existing tables.
    Does not delete or truncate any existing database records.
    """
    try:
        logger.info("Initializing database schema on target SQLite file...")
        Base.metadata.create_all(bind=engine)
        migrate_db()
        logger.info("Database schema verification and initialization completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {str(e)}", exc_info=True)
        return False
