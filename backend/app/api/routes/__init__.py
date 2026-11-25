from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.companies import router as companies_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.system import router as system_router
from app.api.routes.scraper import router as scraper_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.portal import router as portal_router
from app.api.routes.discovery import router as discovery_router
from app.api.routes.extraction import router as extraction_router
from app.api.routes.processing import router as processing_router
from app.api.routes.exports import router as exports_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(dashboard_router)
api_router.include_router(companies_router)
api_router.include_router(jobs_router)
api_router.include_router(sessions_router)
api_router.include_router(system_router)
api_router.include_router(scraper_router)
api_router.include_router(analytics_router)
api_router.include_router(portal_router)
api_router.include_router(discovery_router)
api_router.include_router(extraction_router)
api_router.include_router(processing_router)
api_router.include_router(exports_router)

__all__ = ["api_router"]
