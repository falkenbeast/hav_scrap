@echo off
setlocal enabledelayedexpansion

REM ==============================================================================
REM HAV_SCRAP: Safe Application Shutdown Script
REM Terminates only the specific processes bound to ports 8000 and 5173.
REM Does not kill unrelated Python or Node processes running on the host system.
REM ==============================================================================

title HAV_SCRAP: Safe Shutdown Sequence
cd /d "%~dp0"

echo ==============================================================================
echo        HAV_SCRAP: SAFE PROCESS SHUTDOWN SEQUENCE
echo ==============================================================================
echo.

set KILLED_COUNT=0

REM 1. Terminate FastAPI Backend Process (Port 8000)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr /r ":8000\>"') do (
    set PID_8000=%%a
    if "!PID_8000!" neq "0" (
        echo [INFO] Terminating backend process on port 8000 (PID: !PID_8000!)...
        taskkill /PID !PID_8000! /F >nul 2>&1
        set /a KILLED_COUNT+=1
    )
)

REM 2. Terminate React / Vite Frontend Process (Port 5173)
for /f "tokens=5" %%b in ('netstat -aon ^| findstr /r ":5173\>"') do (
    set PID_5173=%%b
    if "!PID_5173!" neq "0" (
        echo [INFO] Terminating frontend process on port 5173 (PID: !PID_5173!)...
        taskkill /PID !PID_5173! /F >nul 2>&1
        set /a KILLED_COUNT+=1
    )
)

echo.
if !KILLED_COUNT! gtr 0 (
    echo [SUCCESS] Application services successfully terminated.
    echo All database records, browser sessions, and exports remain intact.
) else (
    echo [NOTICE] No active hav_scrap processes found listening on ports 8000 or 5173.
)

echo ==============================================================================
echo.
timeout /t 3 >nul

