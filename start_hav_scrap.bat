@echo off
setlocal enabledelayedexpansion

REM ==============================================================================
REM HAV_SCRAP: Haveloc Placement Intelligence System - Startup Script
REM ==============================================================================

title HAV_SCRAP: Control Deck Launcher
cd /d "%~dp0"

echo ==============================================================================
echo       HAV_SCRAP: HAVELOC PLACEMENT INTELLIGENCE COMMAND DECK
echo ==============================================================================
echo.

REM 1. Verify Virtual Environment
if not exist "backend\venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at backend\venv\Scripts\python.exe!
    echo Please create the virtual environment before launching:
    echo   python -m venv backend\venv
    echo   backend\venv\Scripts\pip install -r backend\requirements.txt
    pause
    exit /b 1
)

REM 2. Verify Frontend Dependencies
if not exist "frontend\node_modules\" (
    echo [WARNING] frontend\node_modules\ not found!
    echo Running npm install in frontend directory...
    call npm --prefix frontend install
    if errorlevel 1 (
        echo [ERROR] Failed to install frontend dependencies.
        pause
        exit /b 1
    )
)

REM 3. Check for Existing Instances (Port 8000 and 5173)
set BACKEND_RUNNING=0
for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r ":8000\>"') do (
    set BACKEND_RUNNING=1
)

if !BACKEND_RUNNING! equ 1 (
    echo [NOTICE] Backend appears to already be running on http://127.0.0.1:8000.
) else (
    echo [INFO] Starting FastAPI Backend Engine on http://127.0.0.1:8000...
    start "HAV_SCRAP Backend (FastAPI)" cmd /c "cd /d "%~dp0" && set PYTHONPATH=backend&& backend\venv\Scripts\python.exe backend\run.py"
)

REM 4. Start Frontend
set FRONTEND_RUNNING=0
for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r ":5173\>"') do (
    set FRONTEND_RUNNING=1
)

if !FRONTEND_RUNNING! equ 1 (
    echo [NOTICE] Frontend appears to already be running on http://localhost:5173.
) else (
    echo [INFO] Starting React Frontend Command Center on http://localhost:5173...
    start "HAV_SCRAP Frontend (Vite)" cmd /c "cd /d "%~dp0\frontend" && npm run dev"
)

echo.
echo ==============================================================================
echo [SUCCESS] HAV_SCRAP PLACEMENT INTELLIGENCE SYSTEM IS OPERATIONAL
echo ==============================================================================
echo.
echo   * React 19 Frontend:   http://localhost:5173
echo   * FastAPI Backend:      http://127.0.0.1:8000
echo   * Interactive API Docs: http://127.0.0.1:8000/api/docs
echo   * Local Database:       data\hav_scrap.db
echo   * Excel Deliverables:   data\exports\
echo   * Rotating Logs:        logs\hav_scrap.log
echo.
echo To gracefully stop all application instances, run: stop_hav_scrap.bat
echo ==============================================================================
echo.
timeout /t 5 >nul

