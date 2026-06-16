@echo off
REM ============================================================
REM  SENTRY - one-click launcher for Windows
REM  Just double-click this file. It installs everything the
REM  first time, then opens the station in your browser.
REM ============================================================
title SENTRY Counter-Surveillance Station
cd /d "%~dp0"

echo.
echo   ===========================================
echo      S E N T R Y   starting up
echo   ===========================================
echo.

REM --- find Python (try py launcher, then python) ---
set PY=
where py >nul 2>nul && set PY=py
if "%PY%"=="" ( where python >nul 2>nul && set PY=python )
if "%PY%"=="" (
  echo   [!] Python is not installed.
  echo.
  echo       1. Go to https://python.org/downloads
  echo       2. Download Python 3 and run the installer
  echo       3. IMPORTANT: check "Add Python to PATH" on the first screen
  echo       4. Then double-click this file again.
  echo.
  pause
  exit /b
)

REM --- first-run setup ---
if not exist ".venv\" (
  echo   First run: setting up ^(about a minute^)...
  %PY% -m venv .venv
)
call .venv\Scripts\activate.bat
echo   Checking dependencies...
python -m pip install --quiet --upgrade pip >nul 2>nul
python -m pip install --quiet -r requirements.txt

echo.
echo   ------------------------------------------------------------
echo    Your laptop's Wi-Fi and Bluetooth work right now.
echo    To add RADIO scanning, plug in an RTL-SDR USB dongle
echo    (~$45) - SENTRY detects it automatically, even while running.
echo   ------------------------------------------------------------
echo.
echo   Launching... your browser will open in a moment.
echo   Keep this window open while using SENTRY. Close it to stop.
echo.
python -m sentry_backend.server
pause
