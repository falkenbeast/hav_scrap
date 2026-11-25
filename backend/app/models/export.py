from datetime import datetime
from sqlalchemy import Integer, String, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, UTCDateTime


class ExportHistory(Base):
    """
    ExportHistory entity representing generated Excel/CSV placement deliverables.
    Tracks filenames, export categories, record counts, file sizes, and generation timestamps.
    """
    __tablename__ = "export_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    export_type: Mapped[str] = mapped_column(String(100), default="ALL", nullable=False, index=True)
    record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="COMPLETED", nullable=False, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_export_created_status", "created_at", "status"),
    )

    def __repr__(self) -> str:
        return f"<ExportHistory id={self.id} filename='{self.filename}' records={self.record_count}>"

