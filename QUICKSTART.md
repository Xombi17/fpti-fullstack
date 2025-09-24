# 🚀 Quick Start Guide - FPTI Dashboard

## Prerequisites
- Python 3.8+ installed
- Virtual environment activated

## Step 1: Activate Virtual Environment
```powershell
# Navigate to project directory
cd C:\Users\varad\Documents\Github\Fpti\fpti

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

## Step 2: Start Backend Server
```powershell
# Open Terminal 1 - Backend
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Step 3: Start Frontend Dashboard
```powershell
# Open Terminal 2 - Frontend (new terminal window)
cd frontend
python app.py
```

## Step 4: Access Your Dashboard
- **Dashboard**: http://127.0.0.1:8050
- **API Documentation**: http://127.0.0.1:8000/docs

## 🎯 One-Command Startup (Alternative)

Create a batch file to start both servers:

```powershell
# Create startup batch file
echo 'cd backend && start "Backend" cmd /k "python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000" && cd ../frontend && start "Frontend" cmd /k "python app.py"' > start_dashboard.bat

# Run the batch file
./start_dashboard.bat
```

## 🛑 To Stop Servers
- Press `Ctrl+C` in each terminal window
- Or close the terminal windows

## 📊 What You'll See
- **Portfolio Overview**: Your investments and net worth
- **Transactions**: Add/view all portfolio transactions  
- **Analytics**: Performance metrics and risk analysis
- **Projections**: Monte Carlo simulations for future planning

## 🔧 Troubleshooting
If you get import errors:
```powershell
pip install -r requirements.txt
```

If database errors occur:
```powershell
cd backend
python -c "from app.database import init_db; init_db()"
```