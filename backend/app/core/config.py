import os
from pathlib import Path
from typing import List, Union, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Workspace Root Directory (resolving strictly via pathlib)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Ensure essential filesystem directories exist on startup
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    """
    Application Settings configuration class.
    Reads values from environment variables or .env file with fallback defaults.
    """
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core Application
    APP_NAME: str = "hav_scrap"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS Allowed Origins
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # Database Configuration (Resolved via pathlib relative to project root)
    DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'hav_scrap.db'}"
    DATABASE_PATH: Path = DATA_DIR / "hav_scrap.db"

    # Storage paths
    DATA_RAW_DIR: Path = DATA_DIR / "raw"
    DATA_PROCESSED_DIR: Path = DATA_DIR / "processed"
    DATA_EXPORTS_DIR: Path = DATA_DIR / "exports"
    DATA_BACKUPS_DIR: Path = DATA_DIR / "backups"
    LOGS_DIR: Path = LOGS_DIR

    # Playwright Browser Binary Configuration (Configurable isolated path & executable path)
    PLAYWRIGHT_BROWSERS_PATH: str = os.getenv("PLAYWRIGHT_BROWSERS_PATH", r"D:\Development\hav_scrap_browsers")
    CHROMIUM_EXECUTABLE_PATH: Optional[str] = os.getenv(
        "CHROMIUM_EXECUTABLE_PATH",
        r"C:\Program Files\Chromium\Application\chrome.exe"
    )
    PLAYWRIGHT_HEADLESS: bool = False
    PLAYWRIGHT_SLOW_MO: int = 100
    PLAYWRIGHT_TIMEOUT: int = 30000

    # Persistent Browser Profile Directory
    BROWSER_PROFILE_DIR: Path = DATA_DIR / "browser_profile"

    # Haveloc Portal Settings (Phase 5 Authentication Target)
    HAVELOC_LOGIN_URL: str = "https://haveloc.com/"
    HAVELOC_TARGET_DASHBOARD_URL: str = "https://placements.haveloc.com/jobs?sort=jobApplyBy%2Cdesc&jobView=eligible"


settings = Settings()

# Ensure sub-storage directories exist
for directory in [
    settings.DATA_RAW_DIR,
    settings.DATA_PROCESSED_DIR,
    settings.DATA_EXPORTS_DIR,
    settings.DATA_BACKUPS_DIR,
    settings.LOGS_DIR,
    settings.BROWSER_PROFILE_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)
