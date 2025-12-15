@echo off
REM Tech Radar Startup Script for Windows

echo.
echo 🚀 Starting Tech Radar...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python from python.org
    pause
    exit /b 1
)

echo 📡 Starting server on port 8000...
echo 🌐 Open your browser to: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start server
python -m http.server 8000
