from datetime import datetime, timezone
from sqlalchemy import TypeDecorator, DateTime
from sqlalchemy.orm import DeclarativeBase


class UTCDateTime(TypeDecorator):
    """
    SQLAlchemy type decorator that guarantees all datetime values
    written to SQLite or read from SQLite are timezone-aware UTC datetimes.
    """
    impl = DateTime
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        return value

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                return value
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value


class Base(DeclarativeBase):
    """
    Base model class for all SQLAlchemy entities in hav_scrap.
    """
    pass

