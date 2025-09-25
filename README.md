# 📊 Financial Portfolio Tracking Interface (FPTI)

<div align="center">

![FPTI Logo](https://img.shields.io/badge/FPTI-Financial%20Portfolio%20Tracker-blue?style=for-the-badge&logo=chart-line)

**A comprehensive financial dashboard for portfolio management, budgeting, and investment analysis**

[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Plotly Dash](https://img.shields.io/badge/Plotly%20Dash-2.14+-purple?style=flat-square&logo=plotly)](https://dash.plotly.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

[🚀 Quick Start](#-quick-start) • [📋 Features](#-features) • [🛠️ Installation](#️-installation) • [📖 Documentation](#-documentation)

</div>

---

## ✨ Overview

FPTI is a modern, full-stack financial management application that provides comprehensive portfolio tracking, budget management, and investment analysis tools. Built with Python, FastAPI, and Plotly Dash, it offers real-time market data integration, advanced analytics, and an intuitive user interface.

### 🎯 Key Highlights

- **Real-time Portfolio Tracking** with live market data
- **Advanced Budget Management** with income and expense tracking
- **Monte Carlo Simulations** for retirement planning
- **Interactive Visualizations** with professional charts and graphs
- **Comprehensive Transaction Management** system
- **Modern UI/UX** with responsive design and animations

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** installed on your system
- **Git** for cloning the repository
- **Virtual environment** (recommended)

### One-Command Setup

```bash
# Clone and setup the project
git clone https://github.com/Xombi17/fpti.git
cd fpti
python -m venv .venv
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
```

### Running the Application

1. **Start the Frontend Dashboard:**
   ```bash
   cd frontend
   python app.py
   ```

2. **Access the Application:**
   - 🌐 **Dashboard**: http://127.0.0.1:8050
   - 📚 **API Docs**: http://127.0.0.1:8000/docs (when backend is running)

## 📋 Features

### 💼 Portfolio Management
- **Real-time Portfolio Valuation** with live price updates
- **Asset Allocation Analysis** with interactive pie charts
- **Performance Tracking** with historical trend analysis
- **Holdings Management** with detailed position tracking
- **P&L Analysis** with gain/loss calculations

### 💰 Budget Management
- **Comprehensive Budget Planning** with category-based tracking
- **Income Source Management** with multiple income streams
- **Expense Tracking** with detailed transaction history
- **Savings Goals** with progress visualization
- **Monthly/Annual Budget Analysis** with variance reporting

### 📈 Advanced Analytics
- **Monte Carlo Simulations** for retirement planning scenarios
- **Asset Correlation Matrix** for diversification analysis
- **Risk Metrics** and performance indicators
- **Market Data Integration** with Yahoo Finance API
- **Net Worth Tracking** with assets and liabilities

### 🎨 User Experience
- **Modern Professional UI** with dark theme
- **Responsive Design** optimized for all screen sizes
- **Interactive Charts** with hover effects and animations
- **Real-time Updates** with automatic data refresh
- **Intuitive Navigation** with tabbed interface

## 🛠️ Installation

### Detailed Setup Instructions

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/fpti.git
   cd fpti
   ```

2. **Create Virtual Environment:**
   ```bash
   python -m venv .venv
   
   # Activate virtual environment
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Setup:**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env file with your configuration
   # Add API keys if needed (Yahoo Finance works without keys)
   ```

5. **Initialize Database (Optional):**
   ```bash
   python setup_sample_data.py
   ```

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.8+ | 3.10+ |
| RAM | 2GB | 4GB+ |
| Storage | 100MB | 500MB+ |
| OS | Windows 10, macOS 10.14, Ubuntu 18.04 | Latest versions |

## 📁 Project Structure

```
fpti/
├── 📂 frontend/                 # Plotly Dash Frontend Application
│   ├── 📄 app.py               # Main dashboard application
│   ├── 📄 yahoo_finance_service.py  # Market data service
│   └── 📂 assets/              # Static assets (CSS, JS, images)
├── 📂 backend/                  # FastAPI Backend (Optional)
│   ├── 📄 main.py              # API entry point
│   ├── 📂 app/                 # Application modules
│   └── 📂 models/              # Database models
├── 📂 data/                     # SQLite database files
├── 📄 requirements.txt          # Python dependencies
├── 📄 .env.example             # Environment variables template
├── 📄 setup_sample_data.py     # Database initialization
└── 📄 README.md                # Project documentation
```

## 🛠️ Tech Stack

### Core Technologies
| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Backend** | FastAPI | 0.104+ | REST API framework |
| **Frontend** | Plotly Dash | 2.14+ | Interactive web dashboard |
| **Database** | SQLite | 3.x | Data persistence |
| **Data Analysis** | Pandas | 2.0+ | Data manipulation |
| **Visualization** | Plotly | 5.15+ | Interactive charts |

### Key Libraries
- **dash-bootstrap-components**: Modern UI components
- **yfinance**: Yahoo Finance market data
- **SQLAlchemy**: Database ORM
- **NumPy & SciPy**: Scientific computing
- **scikit-learn**: Machine learning utilities

## 📖 Documentation

### Application Modules

#### 🎯 Dashboard (`/`)
- Portfolio overview with key metrics
- Asset allocation charts
- Performance summaries
- Recent transactions

#### 📊 Analysis (`/analysis`)
- Correlation matrix analysis
- Risk metrics and performance indicators
- Sector allocation breakdown
- Historical performance tracking

#### 💳 Transactions (`/transactions`)
- Transaction entry and management
- Portfolio-wise transaction filtering
- Transaction history with search

#### 🎲 Monte Carlo (`/monte-carlo`)
- Retirement planning simulations
- Configurable parameters
- Probability distributions
- Success rate analysis

#### 📈 Market Data (`/market-data`)
- Live stock quotes and prices
- Intraday charts with technical indicators
- Symbol search functionality
- Market summary dashboard

#### 🏦 Net Worth (`/net-worth`)
- Assets and liabilities tracking
- Net worth trend analysis
- Category-wise breakdown
- Growth projections

#### � Budgeting (`/budgeting`)
- Budget creation and management
- Income source tracking
- Expense categorization
- Savings goals monitoring

### API Endpoints (Backend)

When running the FastAPI backend, the following endpoints are available:

```
GET  /api/v1/portfolios         # List all portfolios
POST /api/v1/portfolios         # Create new portfolio
GET  /api/v1/transactions       # Get transactions
POST /api/v1/transactions       # Add transaction
GET  /api/v1/market-data/{symbol} # Get market data
```

## 🚦 Usage Examples

### Adding a New Transaction
```python
# Example of programmatic transaction addition
transaction_data = {
    "portfolio_id": 1,
    "symbol": "AAPL",
    "transaction_type": "BUY",
    "quantity": 10,
    "price": 150.00,
    "date": "2024-01-15"
}
```

### Monte Carlo Configuration
```python
# Simulation parameters
monte_carlo_params = {
    "target_value": 10000000,  # ₹1 crore
    "years": 15,
    "monthly_sip": 25000,
    "simulations": 1000
}
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Application Settings
DEBUG=True
ENVIRONMENT=development

# Database Configuration
DATABASE_URL=sqlite:///./data/fpti.db

# API Keys (Optional - Yahoo Finance works without keys)
ALPHA_VANTAGE_API_KEY=your_api_key_here
FINNHUB_API_KEY=your_api_key_here

# Security
SECRET_KEY=your-secret-key-here
```

### Customization Options

- **Theme**: Modify CSS variables in `assets/style.css`
- **Data Sources**: Configure market data providers in settings
- **Currencies**: Support for INR and USD (extensible)
- **Portfolios**: Multiple portfolio support with categorization

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the Repository**
2. **Create Feature Branch**: `git checkout -b feature/amazing-feature`
3. **Commit Changes**: `git commit -m 'Add amazing feature'`
4. **Push Branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

### Development Guidelines
- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation as needed
- Ensure compatibility with Python 3.8+

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/fpti/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/fpti/discussions)
- **Email**: your.email@example.com

## 🎯 Roadmap

### Upcoming Features
- [ ] **Mobile App** with React Native
- [ ] **Multi-currency Support** with real-time conversion
- [ ] **Advanced Charting** with technical indicators
- [ ] **Portfolio Optimization** algorithms
- [ ] **Tax Planning** and reporting tools
- [ ] **Social Features** for investment communities

### Recent Updates
- ✅ **v2.0**: Complete UI/UX redesign with modern theme
- ✅ **v1.5**: Budget management system implementation
- ✅ **v1.2**: Monte Carlo simulation integration
- ✅ **v1.0**: Initial release with portfolio tracking

---

<div align="center">

**⭐ Star this repository if you find it helpful!**

*Built with ❤️ using Python, FastAPI, and Plotly Dash*

[🔝 Back to Top](#-financial-portfolio-tracking-interface-fpti)

</div>