"""
HAV_SCRAP Backend Server Launcher.
Guarantees Windows ProactorEventLoop initialization before Uvicorn starts.
"""
import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.loop import setup_windows_event_loop
setup_windows_event_loop()

from app.core.config import settings
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        loop="asyncio",
        access_log=True,
    )

