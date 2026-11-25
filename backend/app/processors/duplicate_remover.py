import logging
from typing import Dict, Any, List, Tuple
from collections import defaultdict
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.job import JobOpportunity
from app.processors.data_cleaner import DataCleaner

logger = logging.getLogger("hav_scrap")


class DuplicateDetector:
    """
    Dedicated duplicate detection engine for companies and job opportunities.
    Guarantees that distinct job notices within the same company are never collapsed.
    """

    @classmethod
    def analyze_company_duplicates(cls, db: Session) -> Dict[str, Any]:
        """
        Detects company records that share identical normalized names.
        """
        companies = db.execute(select(Company)).scalars().all()
        normalized_map = defaultdict(list)

        for comp in companies:
            norm_name = DataCleaner.clean_company_name(comp.company_name) or comp.company_name.strip().lower()
            normalized_map[norm_name.lower()].append(comp)

        duplicate_clusters = []
        for norm_name, cluster in normalized_map.items():
            if len(cluster) > 1:
                duplicate_clusters.append({
                    "normalized_name": norm_name,
                    "count": len(cluster),
                    "company_ids": [c.id for c in cluster],
                    "raw_names": [c.company_name for c in cluster]
                })

        logger.info(f"Duplicate company analysis: {len(duplicate_clusters)} clusters identified.")
        return {
            "total_companies_checked": len(companies),
            "duplicate_clusters_count": len(duplicate_clusters),
            "duplicate_records_count": sum(c["count"] - 1 for c in duplicate_clusters),
            "clusters": duplicate_clusters
        }

    @classmethod
    def analyze_job_duplicates(cls, db: Session) -> Dict[str, Any]:
        """
        Detects job opportunities sharing identical source URLs or (company_id, cleaned_title, batch).
        Different job profiles at the same company remain strictly separate.
        """
        jobs = db.execute(select(JobOpportunity)).scalars().all()
        url_map = defaultdict(list)
        composite_map = defaultdict(list)

        for job in jobs:
            if job.source_url:
                url_map[job.source_url.strip()].append(job)

            title_key = (
                job.company_id,
                (job.cleaned_job_title or job.job_title).strip().lower(),
                (job.batch or "").strip().lower()
            )
            composite_map[title_key].append(job)

        duplicate_url_clusters = [
            {"source_url": url, "job_ids": [j.id for j in cluster], "count": len(cluster)}
            for url, cluster in url_map.items() if len(cluster) > 1
        ]

        duplicate_composite_clusters = [
            {
                "company_id": key[0],
                "job_title": key[1],
                "batch": key[2],
                "job_ids": [j.id for j in cluster],
                "count": len(cluster)
            }
            for key, cluster in composite_map.items() if len(cluster) > 1
        ]

        logger.info(
            f"Duplicate job analysis: {len(duplicate_url_clusters)} URL duplicates, "
            f"{len(duplicate_composite_clusters)} composite duplicates."
        )

        return {
            "total_jobs_checked": len(jobs),
            "duplicate_url_clusters": duplicate_url_clusters,
            "duplicate_composite_clusters": duplicate_composite_clusters,
            "total_duplicates_detected": len(duplicate_url_clusters) + len(duplicate_composite_clusters),
        }

