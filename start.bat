@echo off
REM FPTI Application Startup Script for Windows

echo Starting FPTI - Financial Portfolio Tracking Interface
echo ======================================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Initialize database
echo Initializing database...
python init_db.py

REM Create sample data
echo Creating sample data...
python create_sample_data.py

echo.
echo Setup complete! Starting services...
echo.

REM Start backend in background
echo Starting backend server...
cd backend
start /B python main.py
cd ..

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend
echo Starting frontend dashboard...
cd frontend
start /B python app.py
cd ..

echo.
echo FPTI is now running!
echo - Backend API: http://localhost:8000
echo - Frontend Dashboard: http://localhost:8050  
echo - API Documentation: http://localhost:8000/docs
echo.
echo Press any key to stop all services
pause >nul

REM Kill Python processes (simple cleanup)
taskkill /F /IM python.exe /T >nul 2>&1

echo Services stopped.
pause