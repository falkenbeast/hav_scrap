from app.core.loop import setup_windows_event_loop
# Ensure Windows uses a subprocess-capable ProactorEventLoop before server initialization
setup_windows_event_loop()

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging_config import setup_logging, logger
from app.database.init_db import init_db
from app.api.routes import api_router
from app.scraper.controller import scraper_controller
from app.services.portal_service import portal_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes database tables, configures rotating logging, and manages graceful shutdowns.
    """
    setup_logging()
    logger.info(f"Initializing {settings.APP_NAME} v{settings.APP_VERSION} (Host: {settings.HOST}:{settings.PORT})...")
    try:
        init_db()
        logger.info("Database schemas verified and ready.")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
    yield
    logger.info(f"Shutting down {settings.APP_NAME}...")
    try:
        await scraper_controller.task_manager.shutdown()
        logger.info("Scraper background tasks safely terminated.")
    except Exception as e:
        logger.warning(f"Exception during scraper shutdown: {e}")
    try:
        await portal_service.disconnect()
        logger.info("Portal browser context safely closed.")
    except Exception as e:
        logger.warning(f"Exception during portal cleanup: {e}")


def create_application() -> FastAPI:
    """
    Factory function to configure and instantiate the hardened FastAPI application.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Haveloc Placement Intelligence System - Central Telemetry & API Engine",
        lifespan=lifespan,
        docs_url=f"{settings.API_PREFIX}/docs" if settings.DEBUG else None,
        redoc_url=f"{settings.API_PREFIX}/redoc" if settings.DEBUG else None,
    )

    # Configure Cross-Origin Resource Sharing (CORS) - strictly allow local frontend origins
    allowed_origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Hardened Global Exception Handler (CWE-209 Protection: Prevents stack trace / path leaks)
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled system fault at {request.url.path}: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "A system error occurred while processing the request. Details have been logged to local rotating audit logs.",
                "path": request.url.path,
            },
        )

    # Mount modular API router under /api
    app.include_router(api_router, prefix=settings.API_PREFIX)

    return app


app = create_application()

if __name__ == "__main__":
    setup_windows_event_loop()
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        loop="asyncio"
    )
