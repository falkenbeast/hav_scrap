"""
Database Backup & Integrity Subsystem.
Safely creates verified, timestamped SQLite snapshot archives in data/backups/,
guaranteeing database preservation, non-destructive operation, and PRAGMA integrity verification.
"""
import logging
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.core.config import settings

logger = logging.getLogger("hav_scrap")


def create_database_backup(tag: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes an atomic online SQLite snapshot backup.
    Verifies that the target backup file exists, has non-zero size, and passes PRAGMA integrity_check.
    Does not delete or alter the original live database.
    """
    settings.DATA_BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    db_source_path = settings.DATABASE_PATH

    if not db_source_path.exists():
        logger.warning(f"Cannot backup: database file does not exist at {db_source_path}")
        return {
            "success": False,
            "error": f"Live database file not found at {db_source_path}",
            "backup_path": None,
            "filename": None,
        }

    # Generate timestamped filename
    timestamp_str = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
    tag_clean = f"_{tag.strip().replace(' ', '_')}" if tag else ""
    filename = f"hav_scrap_backup_{timestamp_str}{tag_clean}.db"
    backup_file_path = settings.DATA_BACKUPS_DIR / filename

    # Avoid overwriting in the unlikely event of collision
    counter = 1
    while backup_file_path.exists():
        filename = f"hav_scrap_backup_{timestamp_str}{tag_clean}_{counter}.db"
        backup_file_path = settings.DATA_BACKUPS_DIR / filename
        counter += 1

    logger.info(f"Initiating online database backup from {db_source_path} to {backup_file_path}...")

    try:
        # Use SQLite's native online backup API for thread-safe snapshotting
        src_conn = sqlite3.connect(str(db_source_path), timeout=30.0)
        dst_conn = sqlite3.connect(str(backup_file_path))

        with dst_conn:
            src_conn.backup(dst_conn, pages=100)

        dst_conn.close()
        src_conn.close()

        # Integrity verification
        if not backup_file_path.exists():
            raise IOError(f"Backup target file was not created: {backup_file_path}")

        file_size = backup_file_path.stat().st_size
        if file_size == 0 and db_source_path.stat().st_size > 0:
            raise IOError("Backup file was created with 0 bytes while source has data.")

        # Run PRAGMA integrity_check on the generated backup
        chk_conn = sqlite3.connect(str(backup_file_path), timeout=10.0)
        cursor = chk_conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        check_result = cursor.fetchone()
        chk_conn.close()

        status_text = check_result[0] if check_result else "unknown"
        if status_text != "ok":
            raise ValueError(f"Backup failed PRAGMA integrity check: {status_text}")

        logger.info(
            f"Database backup verified successfully: {filename} "
            f"({file_size} bytes, integrity: {status_text})."
        )

        return {
            "success": True,
            "filename": filename,
            "backup_path": str(backup_file_path),
            "file_size_bytes": file_size,
            "integrity": status_text,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    except Exception as e:
        logger.error(f"Database backup fault: {str(e)}", exc_info=True)
        # If backup failed or is corrupted, remove partial file
        if backup_file_path.exists():
            try:
                backup_file_path.unlink()
            except Exception:
                pass
        return {
            "success": False,
            "error": str(e),
            "backup_path": None,
            "filename": None,
        }


def list_database_backups() -> List[Dict[str, Any]]:
    """
    Returns list of all verified timestamped database backups stored in data/backups/.
    """
    if not settings.DATA_BACKUPS_DIR.exists():
        return []

    backups = []
    for file in sorted(settings.DATA_BACKUPS_DIR.glob("hav_scrap_backup_*.db"), reverse=True):
        if file.is_file():
            stat = file.stat()
            backups.append({
                "filename": file.name,
                "file_path": str(file),
                "file_size_bytes": stat.st_size,
                "created_at": datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z",
            })

    return backups

