import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.session import ScrapingSession
from app.database.session import SessionLocal

logger = logging.getLogger("hav_scrap")

# Valid lifecycle state definitions and transition rules
VALID_STATES = {
    "IDLE",
    "INITIALIZING",
    "RUNNING",
    "PAUSED",
    "STOPPING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
}

ALLOWED_TRANSITIONS = {
    "IDLE": {"INITIALIZING", "RUNNING"},
    "INITIALIZING": {"RUNNING", "FAILED", "CANCELLED", "STOPPING"},
    "RUNNING": {"PAUSED", "STOPPING", "COMPLETED", "FAILED"},
    "PAUSED": {"RUNNING", "STOPPING", "CANCELLED", "FAILED"},
    "STOPPING": {"CANCELLED", "FAILED", "COMPLETED"},
    "COMPLETED": {"IDLE", "INITIALIZING"},
    "FAILED": {"IDLE", "INITIALIZING"},
    "CANCELLED": {"IDLE", "INITIALIZING"},
}


class InvalidStateTransitionError(Exception):
    """Raised when an illegal scraping session state transition is attempted."""
    pass


class SessionManager:
    """
    Manages the database lifecycle and persistence of ScrapingSession records in SQLite,
    strictly validating all state transitions.
    """

    @staticmethod
    def is_valid_transition(current_state: str, new_state: str) -> bool:
        if current_state not in ALLOWED_TRANSITIONS:
            return False
        return new_state in ALLOWED_TRANSITIONS[current_state]

    @classmethod
    def create_session(cls, initial_status: str = "INITIALIZING") -> ScrapingSession:
        """
        Creates a new ScrapingSession record in the database.
        Ensures any previous dangling 'RUNNING' session is safely marked 'FAILED'.
        """
        with SessionLocal() as db:
            # Check for dangling active sessions
            dangling = db.query(ScrapingSession).filter(
                ScrapingSession.status.in_(["RUNNING", "INITIALIZING", "PAUSED", "STOPPING"])
            ).all()

            for s in dangling:
                logger.warning(f"Closing dangling session #{s.id} in state '{s.status}' before starting new run.")
                s.status = "CANCELLED"
                s.completed_at = datetime.now(timezone.utc)
                s.error_message = "Automatically cancelled by system prior to new session initialization."

            session = ScrapingSession(
                status=initial_status,
                started_at=datetime.now(timezone.utc),
                records_discovered=0,
                records_processed=0,
                error_message=None
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            logger.info(f"Initialized ScrapingSession #{session.id} with status '{initial_status}'")
            return session

    @classmethod
    def transition_status(
        cls,
        session_id: int,
        new_status: str,
        error_message: Optional[str] = None
    ) -> ScrapingSession:
        """
        Enforces state transition rules and updates session record.
        """
        if new_status not in VALID_STATES:
            raise ValueError(f"Unknown session state: {new_status}")

        with SessionLocal() as db:
            session = db.query(ScrapingSession).filter(ScrapingSession.id == session_id).first()
            if not session:
                raise ValueError(f"ScrapingSession #{session_id} not found in database.")

            if not cls.is_valid_transition(session.status, new_status):
                err = f"Illegal state transition for Session #{session_id}: '{session.status}' -> '{new_status}'"
                logger.error(err)
                raise InvalidStateTransitionError(err)

            session.status = new_status
            if error_message:
                session.error_message = error_message

            if new_status in {"COMPLETED", "FAILED", "CANCELLED"}:
                session.completed_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(session)
            logger.info(f"ScrapingSession #{session_id} transitioned to '{new_status}'")
            return session

    @classmethod
    def update_metrics(
        cls,
        session_id: int,
        records_discovered: Optional[int] = None,
        records_processed: Optional[int] = None
    ) -> Optional[ScrapingSession]:
        """
        Updates discovered and processed counters for an active session.
        """
        with SessionLocal() as db:
            session = db.query(ScrapingSession).filter(ScrapingSession.id == session_id).first()
            if not session:
                return None

            if records_discovered is not None:
                session.records_discovered = records_discovered
            if records_processed is not None:
                session.records_processed = records_processed

            db.commit()
            db.refresh(session)
            return session

    @classmethod
    def get_session(cls, session_id: int) -> Optional[ScrapingSession]:
        with SessionLocal() as db:
            return db.query(ScrapingSession).filter(ScrapingSession.id == session_id).first()

    @classmethod
    def get_latest_session(cls) -> Optional[ScrapingSession]:
        with SessionLocal() as db:
            return db.query(ScrapingSession).order_by(ScrapingSession.started_at.desc()).first()

    @classmethod
    def get_sessions_history(cls, skip: int = 0, limit: int = 20) -> Tuple[List[ScrapingSession], int]:
        with SessionLocal() as db:
            query = db.query(ScrapingSession).order_by(ScrapingSession.started_at.desc())
            total = db.query(func.count(ScrapingSession.id)).scalar() or 0
            items = query.offset(skip).limit(limit).all()
            return items, total

