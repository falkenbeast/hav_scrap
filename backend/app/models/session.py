from datetime import datetime
from sqlalchemy import Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, UTCDateTime


class ScrapingSession(Base):
    """
    ScrapingSession entity tracks telemetry, audit history, and execution metrics of the scraping engine.
    """
    __tablename__ = "scraping_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(50), default="IDLE", index=True, nullable=False)
    # Statuses: IDLE, PENDING, RUNNING, COMPLETED, FAILED, TERMINATED

    started_at: Mapped[datetime] = mapped_column(UTCDateTime, default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    records_discovered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ScrapingSession id={self.id} status='{self.status}' discovered={self.records_discovered}>"
