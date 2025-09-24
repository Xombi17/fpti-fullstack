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

- **Modern Professional UI/UX**: Sleek financial dashboard with animations, gradients, and responsive design
- **Portfolio Dashboard**: Real-time portfolio valuation with animated metric cards and professional styling
- **Interactive Charts**: Beautiful asset allocation, performance trends, and correlation matrices with modern color schemes
- **Monte Carlo Simulations**: Interactive retirement planning with professional histogram visualizations
- **Market Data Integration**: Live price updates with elegant data tables and hover effects
- **Transaction Management**: Intuitive forms with modern styling and smooth animations

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
- **Frontend**: Plotly Dash, Bootstrap Components, Custom CSS3
- **Database**: SQLite (Production-ready ACID compliant)
- **APIs**: Yahoo Finance market data
- **UI/UX**: Modern CSS Grid, Inter Font, Professional Color Palette, Smooth Animations

## 🛑 To Stop Servers

Press `Ctrl+C` in each terminal window to stop the servers.

---

*Built with Python • FastAPI • Plotly Dash*