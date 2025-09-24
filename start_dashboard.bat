@echo off
echo Starting FPTI Financial Dashboard...
echo.

REM Start backend server in new window
echo Starting Backend API Server...
start "FPTI Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend dashboard in new window  
echo Starting Frontend Dashboard...
start "FPTI Frontend" cmd /k "cd /d %~dp0frontend && python app.py"

echo.
echo Dashboard starting...
echo Backend API: http://127.0.0.1:8000
echo Frontend Dashboard: http://127.0.0.1:8050
echo.
echo Press any key to open dashboard in browser...
pause >nul

REM Open dashboard in default browser
start http://127.0.0.1:8050

echo Dashboard launched! Close this window when done.
pause