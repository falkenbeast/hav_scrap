from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, Float, Text, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, UTCDateTime

if TYPE_CHECKING:
    from app.models.company import Company


class JobOpportunity(Base):
    """
    JobOpportunity entity representing individual job notices, profiles, and compensation packages.
    """
    __tablename__ = "job_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    job_title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    job_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Salary Intelligence Attributes (Phase 7 Normalized)
    original_salary_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    minimum_ctc: Mapped[float | None] = mapped_column(Float, nullable=True)
    maximum_ctc: Mapped[float | None] = mapped_column(Float, nullable=True)
    fixed_ctc: Mapped[float | None] = mapped_column(Float, nullable=True)
    variable_ctc: Mapped[float | None] = mapped_column(Float, nullable=True)
    joining_bonus: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_lpa: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    salary_unit: Mapped[str | None] = mapped_column(String(50), default="LPA", nullable=True)
    stipend_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    stipend_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    stipend_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    original_stipend_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stipend_period: Mapped[str | None] = mapped_column(String(50), nullable=True)
    annualized_equivalent: Mapped[float | None] = mapped_column(Float, nullable=True)
    annualized_equivalent_lpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # FIXED_CTC, CTC_RANGE, etc.

    # Opportunity Details
    job_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)  # Full-Time, Internship, 6M+FTE
    job_status: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)  # Portal status: Closed For Applications, etc.
    work_mode: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # Remote, Hybrid, Onsite
    location: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    eligibility: Mapped[str | None] = mapped_column(Text, nullable=True)
    minimum_cgpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    eligible_branches: Mapped[str | None] = mapped_column(Text, nullable=True)
    backlog_criteria: Mapped[str | None] = mapped_column(String(255), nullable=True)
    academic_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    batch: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    # Cleaned & Validated Attributes (Phase 8)
    cleaned_job_title: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    cleaned_company_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    validation_status: Mapped[str | None] = mapped_column(String(50), default="VALID", nullable=True, index=True)
    validation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metadata & Tracking
    application_deadline: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    date_of_visit: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    posted_date: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True, index=True)
    extraction_status: Mapped[str | None] = mapped_column(String(50), default="PENDING", nullable=True, index=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to parent company
    company: Mapped["Company"] = relationship("Company", back_populates="jobs")

    __table_args__ = (
        Index("ix_job_company_title_batch", "company_id", "job_title", "batch"),
    )

    def __repr__(self) -> str:
        return f"<JobOpportunity id={self.id} title='{self.job_title}' ctc='{self.salary_lpa} LPA'>"
