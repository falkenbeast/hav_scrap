from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import Integer, String, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, UTCDateTime

if TYPE_CHECKING:
    from app.models.job import JobOpportunity


class Company(Base):
    """
    Company entity representing an organization registered on the Haveloc placement portal.
    """
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    description: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # One Company can have multiple JobOpportunity records
    jobs: Mapped[List["JobOpportunity"]] = relationship(
        "JobOpportunity",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Company id={self.id} name='{self.company_name}'>"
