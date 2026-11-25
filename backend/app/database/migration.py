import logging
from sqlalchemy import text
from app.database.session import engine

logger = logging.getLogger("hav_scrap")


def migrate_db():
    """
    Non-destructive SQLite schema migrator for Phase 7.
    Inspects existing database columns via PRAGMA table_info and executes
    ALTER TABLE ... ADD COLUMN for any newly introduced columns.
    Guarantees 100% preservation of all previously collected database records.
    """
    column_definitions = {
        "companies": [
            ("description", "TEXT"),
            ("industry", "VARCHAR(255)"),
        ],
        "job_opportunities": [
            ("job_description", "TEXT"),
            ("work_mode", "VARCHAR(50)"),
            ("joining_bonus", "FLOAT"),
            ("stipend_amount", "FLOAT"),
            ("stipend_period", "VARCHAR(50)"),
            ("annualized_equivalent", "FLOAT"),
            ("backlog_criteria", "VARCHAR(255)"),
            ("academic_criteria", "TEXT"),
            ("application_deadline", "DATETIME"),
            ("extraction_status", "VARCHAR(50) DEFAULT 'PENDING'"),
            ("last_verified_at", "DATETIME"),
            ("annualized_equivalent_lpa", "FLOAT"),
            ("salary_type", "VARCHAR(50)"),
            ("cleaned_job_title", "VARCHAR(255)"),
            ("cleaned_company_name", "VARCHAR(255)"),
            ("validation_status", "VARCHAR(50) DEFAULT 'VALID'"),
            ("validation_notes", "TEXT"),
            ("original_stipend_text", "VARCHAR(255)"),
            ("stipend_min", "FLOAT"),
            ("stipend_max", "FLOAT"),
            ("date_of_visit", "DATETIME"),
            ("job_status", "VARCHAR(100)"),
        ]
    }

    try:
        with engine.connect() as conn:
            for table_name, columns in column_definitions.items():
                # Check if table exists
                table_check = conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table"),
                    {"table": table_name}
                ).fetchone()

                if not table_check:
                    continue  # Table will be created by Base.metadata.create_all

                # Retrieve existing column names
                existing_cols_info = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
                existing_col_names = {row[1].lower() for row in existing_cols_info}

                for col_name, col_type in columns:
                    if col_name.lower() not in existing_col_names:
                        logger.info(f"Adding new column '{col_name}' ({col_type}) to table '{table_name}'...")
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                        logger.info(f"Successfully migrated column '{col_name}' into '{table_name}'.")

        logger.info("Non-destructive SQLite migration verified successfully.")
        return True
    except Exception as e:
        logger.error(f"Migration error during schema evolution: {str(e)}", exc_info=True)
        return False

