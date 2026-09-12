@echo off
setlocal enabledelayedexpansion
title SkillBridge MVP Server

echo ===========================================================
echo            SkillBridge MVP - Local Server Launcher
echo ===========================================================
echo.

:: 1. Navigate to the project root containing backend\main.py
cd /d "%~dp0"

if exist "backend\main.py" (
    set "PROJECT_DIR=!cd!"
) else if exist "SkillBridge-MVP\backend\main.py" (
    cd /d "%~dp0SkillBridge-MVP"
    set "PROJECT_DIR=!cd!"
) else (
    echo [ERROR] Could not locate backend\main.py.
    echo Please make sure this batch file is inside the SkillBridge-MVP project folder.
    echo.
    pause
    exit /b 1
)

echo [INFO] Working directory: !PROJECT_DIR!

:: 2. Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python was not found in your system PATH.
    echo Please download and install Python from https://www.python.org/
    echo Remember to check "Add python.exe to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set "PY_VER=%%i"
echo [INFO] Detected !PY_VER!

:: 3. Activate virtual environment if present
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment .venv...
    call ".venv\Scripts\activate.bat"
) else if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment venv...
    call "venv\Scripts\activate.bat"
)

:: 4. Verify dependencies
python -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [INFO] Required packages not found. Installing from requirements.txt...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies from requirements.txt.
        echo Please check your internet connection or run 'pip install -r requirements.txt' manually.
        echo.
        pause
        exit /b 1
    )
    echo [INFO] Dependencies installed successfully.
)

:: 5. Launch browser automatically in background after 2 seconds
start /b "" cmd /c "ping 127.0.0.1 -n 3 >nul && start http://localhost:8000"

echo.
echo ===========================================================
echo  SkillBridge Server is starting...
echo ===========================================================
echo  * Web App:     http://localhost:8000
echo  * Legacy Demo: http://localhost:8000/legacy
echo  * Leaderboard: http://localhost:8000/leaderboard
echo  * API Docs:    http://localhost:8000/docs
echo.
echo  Opening browser automatically at http://localhost:8000 ...
echo  Press Ctrl+C in this window to stop the server.
echo ===========================================================
echo.

:: 6. Run FastAPI application with hot reloading enabled
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

if errorlevel 1 (
    echo.
    echo [INFO] Server stopped.
    pause
)
