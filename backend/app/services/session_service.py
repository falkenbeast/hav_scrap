from typing import List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.session import ScrapingSession
from app.schemas.session import ScrapingSessionResponse, ScrapingSessionUpdate


class SessionService:
    @staticmethod
    def get_sessions(
        db: Session,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[ScrapingSessionResponse], int]:
        """
        Retrieves paginated scraping session audit history.
        """
        query = db.query(ScrapingSession).order_by(ScrapingSession.started_at.desc())
        total = db.query(func.count(ScrapingSession.id)).scalar() or 0
        sessions = query.offset(skip).limit(limit).all()
        return [ScrapingSessionResponse.model_validate(s) for s in sessions], total

    @staticmethod
    def get_latest_session(db: Session) -> Optional[ScrapingSessionResponse]:
        latest = db.query(ScrapingSession).order_by(ScrapingSession.started_at.desc()).first()
        if not latest:
            return None
        return ScrapingSessionResponse.model_validate(latest)

    @staticmethod
    def get_session_by_id(db: Session, session_id: int) -> Optional[ScrapingSessionResponse]:
        session = db.query(ScrapingSession).filter(ScrapingSession.id == session_id).first()
        if not session:
            return None
        return ScrapingSessionResponse.model_validate(session)

    @staticmethod
    def create_session(db: Session, status: str = "IDLE") -> ScrapingSession:
        new_session = ScrapingSession(
            status=status,
            records_discovered=0,
            records_processed=0
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session

    @staticmethod
    def terminate_session(db: Session, session_id: int, message: str = "Terminated by operator") -> Optional[ScrapingSession]:
        session = db.query(ScrapingSession).filter(ScrapingSession.id == session_id).first()
        if not session:
            return None
        session.status = "TERMINATED"
        session.completed_at = datetime.now(timezone.utc)
        session.error_message = message
        db.commit()
        db.refresh(session)
        return session

