@echo off
REM Windows Installation Script with Pandas Fix

echo FPTI Windows Installation Script
echo ==================================

REM Check Python version
python --version
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo.
echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Error creating virtual environment
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Upgrading pip and setuptools...
python -m pip install --upgrade pip setuptools wheel

echo.
echo Installing pandas and numpy first (pre-compiled wheels)...
pip install pandas numpy --only-binary=all --no-build-isolation

echo.
echo Installing remaining dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo Some packages failed to install. Trying alternative approach...
    echo Installing core packages individually...
    
    pip install fastapi uvicorn[standard] sqlalchemy pydantic
    pip install plotly dash dash-bootstrap-components
    pip install yfinance requests python-dotenv
    pip install pytest black flake8
    
    echo.
    echo Core packages installed. Some optional packages may have been skipped.
)

echo.
echo Initializing database...
python init_db.py

echo.
echo Creating sample data...
python create_sample_data.py

echo.
echo Installation complete!
echo.
echo To start the application:
echo 1. Backend: cd backend && python main.py
echo 2. Frontend: cd frontend && python app.py
echo 3. Visit: http://localhost:8050
echo.
pause