# Financial Portfolio Tracking Interface (FPTI)

A full-stack financial dashboard built with Python, FastAPI, and Plotly Dash.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Virtual environment activated

### Running the Application

**Start Backend Server:**
```bash
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Start Frontend Dashboard (new terminal):**
```bash
cd frontend
python app.py
```

### Access the Application
- **Dashboard**: http://127.0.0.1:8050
- **API Documentation**: http://127.0.0.1:8000/docs

## 🎯 Features

- **Portfolio Dashboard**: Real-time portfolio valuation and performance tracking
- **Interactive Charts**: Asset allocation, performance trends, holdings analysis  
- **Monte Carlo Simulations**: Retirement planning and risk assessment
- **Market Data Integration**: Live price updates from Yahoo Finance
- **Transaction Management**: Complete portfolio transaction history

## 📁 Project Structure

```
fpti/
├── backend/           # FastAPI Backend API
│   ├── app/          # Application modules
│   └── main.py       # API entry point
├── frontend/         # Plotly Dash Frontend
│   └── app.py        # Dashboard application
├── data/            # SQLite database
├── .venv/           # Virtual environment
└── requirements.txt # Dependencies
```

## 🛠️ Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Pandas
- **Frontend**: Plotly Dash, Bootstrap Components
- **Database**: SQLite
- **APIs**: Yahoo Finance market data

## 🛑 To Stop Servers

Press `Ctrl+C` in each terminal window to stop the servers.

---

*Built with Python • FastAPI • Plotly Dash*