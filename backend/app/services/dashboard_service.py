from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.company import Company
from app.models.job import JobOpportunity
from app.models.session import ScrapingSession
from app.models.export import ExportHistory
from app.schemas.stats import DashboardStatsResponse


class DashboardService:
    @staticmethod
    def get_dashboard_stats(db: Session) -> DashboardStatsResponse:
        """
        Calculates real aggregated statistics from persistent database records.
        """
        total_companies = db.query(func.count(Company.id)).scalar() or 0
        total_jobs = db.query(func.count(JobOpportunity.id)).scalar() or 0

        # CTC aggregates (only for non-null salary_lpa)
        avg_ctc = db.query(func.avg(JobOpportunity.salary_lpa)).filter(
            JobOpportunity.salary_lpa.isnot(None),
            JobOpportunity.salary_lpa > 0
        ).scalar() or 0.0

        highest_ctc = db.query(func.max(JobOpportunity.salary_lpa)).filter(
            JobOpportunity.salary_lpa.isnot(None)
        ).scalar() or 0.0

        lowest_ctc = db.query(func.min(JobOpportunity.salary_lpa)).filter(
            JobOpportunity.salary_lpa.isnot(None),
            JobOpportunity.salary_lpa > 0
        ).scalar() or 0.0

        # Job type breakdown
        full_time_jobs = db.query(func.count(JobOpportunity.id)).filter(
            JobOpportunity.job_type.ilike("%full%") | JobOpportunity.job_type.ilike("%fte%")
        ).scalar() or 0

        internship_jobs = db.query(func.count(JobOpportunity.id)).filter(
            JobOpportunity.job_type.ilike("%intern%")
        ).scalar() or 0

        total_sessions = db.query(func.count(ScrapingSession.id)).scalar() or 0

        active_sessions = db.query(func.count(ScrapingSession.id)).filter(
            ScrapingSession.status.in_(["RUNNING", "PENDING"])
        ).scalar() or 0

        latest_session = db.query(ScrapingSession).order_by(ScrapingSession.started_at.desc()).first()
        last_scrape = latest_session.started_at.strftime("%Y-%m-%d %H:%M") if latest_session else None

        avg_ctc_rounded = round(float(avg_ctc), 2)
        highest_ctc_rounded = round(float(highest_ctc), 2)
        lowest_ctc_rounded = round(float(lowest_ctc), 2)

        return DashboardStatsResponse(
            total_companies=total_companies,
            total_jobs=total_jobs,
            average_ctc=avg_ctc_rounded,
            highest_ctc=highest_ctc_rounded,
            lowest_ctc=lowest_ctc_rounded,
            full_time_jobs=full_time_jobs,
            internship_jobs=internship_jobs,
            total_scraping_sessions=total_sessions,
            avg_salary_lpa=avg_ctc_rounded,
            highest_salary_lpa=highest_ctc_rounded,
            last_scrape_time=last_scrape,
            active_sessions=active_sessions
        )

    @staticmethod
    def get_recent_activity(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieves real-time intelligence activities from persistent SQLite records:
        - Job discoveries
        - Company profiles indexed
        - Scraping sessions executed
        - Placement deliverables exported
        Returns an empty list if no activities have occurred. No fabricated data.
        """
        events: List[Dict[str, Any]] = []

        min_dt = datetime.min.replace(tzinfo=timezone.utc)

        # 1. Recent Scraping Sessions
        sessions = db.query(ScrapingSession).order_by(ScrapingSession.started_at.desc()).limit(limit).all()
        for s in sessions:
            dt = s.completed_at or s.started_at
            status_variant = "success" if s.status == "COMPLETED" else ("danger" if s.status in ("FAILED", "TERMINATED") else "warning")
            events.append({
                "id": f"session-{s.id}",
                "type": "extraction_completed" if s.status == "COMPLETED" else "system_init",
                "title": f"Reconnaissance Session #{s.id} [{s.status}]",
                "description": f"Discovered {s.records_discovered} postings, processed {s.records_processed} records." + (f" Notice: {s.error_message}" if s.error_message else ""),
                "timestamp": dt.isoformat() if dt else "Recent",
                "badge": s.status,
                "badgeVariant": status_variant,
                "_sort_key": dt if dt else min_dt
            })

        # 2. Recent Company Discoveries
        companies = db.query(Company).order_by(Company.created_at.desc()).limit(limit).all()
        for c in companies:
            events.append({
                "id": f"company-{c.id}",
                "type": "company_discovery",
                "title": f"Recruiter Profile Discovered: {c.company_name}",
                "description": f"Verified corporate entry registered in local placement repository. Industry: {c.industry or 'General Tech'}.",
                "timestamp": c.created_at.isoformat() if c.created_at else "Recent",
                "badge": "DISCOVERY",
                "badgeVariant": "cyan",
                "_sort_key": c.created_at if c.created_at else min_dt
            })

        # 3. Recent Job Postings
        jobs = db.query(JobOpportunity).order_by(JobOpportunity.created_at.desc()).limit(limit).all()
        for j in jobs:
            c_name = j.company.company_name if j.company else "Recruiter"
            salary_str = f"{j.salary_lpa} LPA CTC" if j.salary_lpa else "Package Unspecified"
            events.append({
                "id": f"job-{j.id}",
                "type": "company_discovery",
                "title": f"Opportunity Indexed: {j.job_title} ({c_name})",
                "description": f"{j.job_type or 'Role'} • {salary_str} • Location: {j.location or 'Flexible'}.",
                "timestamp": j.created_at.isoformat() if j.created_at else "Recent",
                "badge": "OPPORTUNITY",
                "badgeVariant": "cyan",
                "_sort_key": j.created_at if j.created_at else min_dt
            })

        # 4. Recent Excel Deliverable Exports
        try:
            exports = db.query(ExportHistory).order_by(ExportHistory.created_at.desc()).limit(limit).all()
            for exp in exports:
                events.append({
                    "id": f"export-{exp.id}",
                    "type": "export_generated",
                    "title": f"Deliverable Exported: {exp.filename}",
                    "description": f"Type: {exp.export_type} • Records: {exp.record_count} • Size: {round(exp.file_size_bytes / 1024, 1)} KB",
                    "timestamp": exp.created_at.isoformat() if exp.created_at else "Recent",
                    "badge": "DELIVERABLE",
                    "badgeVariant": "orange",
                    "_sort_key": exp.created_at if exp.created_at else min_dt
                })
        except Exception:
            pass

        # Sort all combined events chronologically descending
        events.sort(key=lambda x: x["_sort_key"], reverse=True)

        # Remove internal sort key and truncate to limit
        final_events = []
        for e in events[:limit]:
            del e["_sort_key"]
            final_events.append(e)

        return final_events


