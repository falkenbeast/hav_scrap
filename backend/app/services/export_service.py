"""
Export Management Service.
Coordinates Excel workbook generation, persistence to data/exports/,
historical deliverable logging in SQLite, and download stream delivery.
"""
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.export import ExportHistory
from app.exporters.excel_exporter import ExcelPlacementExporter

logger = logging.getLogger("hav_scrap")


class ExportService:
    """
    Manages end-to-end placement data exports and deliverable lifecycle.
    """

    def __init__(self):
        self.exports_dir = settings.DATA_EXPORTS_DIR
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.exporter = ExcelPlacementExporter(self.exports_dir)

    def generate_export(
        self,
        db: Session,
        export_type: str = "ALL",
        include_sheets: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        custom_filename: Optional[str] = None
    ) -> ExportHistory:
        """
        Executes placement intelligence export pipeline, creating an OpenPyXL
        workbook and persisting an audit record in the database.
        """
        logger.info(f"Initiating placement Excel export [Type: {export_type}]...")

        # Sanitize custom_filename to strip directory traversal sequences
        safe_custom_filename = None
        if custom_filename:
            safe_custom_filename = Path(custom_filename).name

        try:
            # Generate workbook using exporter
            result = self.exporter.generate_workbook(
                db=db,
                export_type=export_type,
                include_sheets=include_sheets,
                custom_filename=safe_custom_filename
            )

            # Record in database
            history = ExportHistory(
                filename=result["filename"],
                export_type=export_type,
                record_count=result["record_count"],
                file_size_bytes=result["file_size_bytes"],
                file_path=result["file_path"],
                status="COMPLETED",
                error_message=None,
                created_at=result["created_at"]
            )
            db.add(history)
            db.commit()
            db.refresh(history)

            logger.info(
                f"Excel export successfully generated: {history.filename} "
                f"({history.record_count} records, {history.file_size_bytes} bytes)."
            )
            return history

        except Exception as e:
            logger.error(f"Failed to generate Excel export: {str(e)}", exc_info=True)
            db.rollback()

            # Record failed export attempt
            timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
            failed_filename = f"FAILED_{export_type}_{timestamp_str}.xlsx"
            history = ExportHistory(
                filename=failed_filename,
                export_type=export_type,
                record_count=0,
                file_size_bytes=0,
                file_path="",
                status="FAILED",
                error_message=str(e),
                created_at=datetime.now(timezone.utc)
            )
            db.add(history)
            db.commit()
            db.refresh(history)
            raise e

    def list_exports(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Retrieves paginated export history records.
        """
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        offset = (page - 1) * page_size

        total = db.execute(select(func.count(ExportHistory.id))).scalar() or 0
        items = db.execute(
            select(ExportHistory)
            .order_by(ExportHistory.created_at.desc())
            .offset(offset)
            .limit(page_size)
        ).scalars().all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    def get_export_by_id(self, db: Session, export_id: int) -> Optional[ExportHistory]:
        """
        Retrieves single export metadata by ID.
        """
        return db.execute(
            select(ExportHistory).where(ExportHistory.id == export_id)
        ).scalar_one_or_none()

    def get_export_file_path(self, db: Session, export_id: int) -> Optional[Path]:
        """
        Resolves physical filesystem path of an export deliverable.
        Strictly prevents directory traversal (CWE-22) outside data/exports/.
        """
        history = self.get_export_by_id(db, export_id)
        if not history or not history.file_path:
            return None

        p = Path(history.file_path).resolve()
        exports_root = self.exports_dir.resolve()

        try:
            # Enforce that path resides strictly inside data/exports
            p.relative_to(exports_root)
        except ValueError:
            logger.critical(f"Security Alert: Directory traversal detected for export ID {export_id}: {history.file_path}")
            return None

        if p.exists() and p.is_file():
            return p
        return None

    def delete_export(self, db: Session, export_id: int) -> bool:
        """
        Removes physical Excel file and deletes database record.
        Strictly prevents directory traversal (CWE-22) outside data/exports/.
        """
        history = self.get_export_by_id(db, export_id)
        if not history:
            return False

        # Attempt to delete file from disk with containment check
        if history.file_path:
            p = Path(history.file_path).resolve()
            exports_root = self.exports_dir.resolve()
            try:
                p.relative_to(exports_root)
                if p.exists() and p.is_file():
                    p.unlink()
                    logger.info(f"Deleted physical export deliverable: {p.name}")
            except ValueError:
                logger.critical(f"Security Alert: Refusing to delete path outside exports directory: {history.file_path}")
            except Exception as ex:
                logger.warning(f"Could not delete physical file: {str(ex)}")

        db.delete(history)
        db.commit()
        return True


export_service = ExportService()

