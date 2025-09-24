# Financial Portfolio Tracking Interface (FPTI)

A comprehensive full-stack financial dashboard built with Python, integrating advanced concepts including OOP, Pandas, Async programming, FastAPI, Plotly Dash, and SQLAlchemy.

## 🎯 Project Overview

This project demonstrates the integration of advanced Python concepts in a real-world financial application:

### Python Concepts Implemented
- **Object-Oriented Programming (OOP)**: Financial instrument classes with inheritance and encapsulation
- **Pandas Data Analysis**: Portfolio performance metrics, returns calculation, and data manipulation
- **Async Programming**: Concurrent market data fetching from external APIs
- **FastAPI Web Framework**: RESTful API endpoints with automatic documentation
- **Plotly Dash Visualization**: Interactive financial dashboards and charts
- **SQLAlchemy ORM**: Database models and relationships

### Financial Concepts
- **Portfolio Management**: Multi-portfolio tracking with asset allocation
- **Net Worth Tracking**: Historical wealth monitoring and projections
- **Investment Performance**: Risk metrics, Sharpe ratio, volatility analysis
- **Monte Carlo Simulations**: Retirement planning and risk assessment
- **Market Data Integration**: Real-time price updates and historical analysis

## 🚀 Features

### Dashboard
- **Real-time Portfolio Valuation**: Live market data integration
- **Interactive Charts**: Asset allocation, performance trends, sector analysis
- **Holdings Management**: Detailed position tracking with P&L
- **Performance Metrics**: Total return, volatility, Sharpe ratio, max drawdown

### Analytics
- **Monte Carlo Simulations**: Retirement probability calculations
- **Risk Analysis**: Concentration risk, liquidity scoring, correlation analysis
- **Portfolio Optimization**: Rebalancing recommendations based on risk tolerance
- **Historical Analysis**: Performance attribution and trend analysis

### Data Management
- **Multi-Portfolio Support**: Separate tracking for different investment strategies
- **Transaction History**: Complete audit trail of all portfolio activity
- **Market Data Caching**: Efficient data retrieval with rate limiting
- **Export Capabilities**: Portfolio data export for external analysis

## 🏗️ Architecture

```
fpti/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── models/            # SQLAlchemy database models
│   │   ├── routers/           # API endpoint definitions
│   │   │   ├── portfolios.py  # Portfolio management
│   │   │   ├── transactions.py # Transaction handling
│   │   │   ├── assets.py      # Asset management
│   │   │   ├── market_data.py # Real-time data
│   │   │   └── analytics.py   # Financial analytics
│   │   ├── services/          # Business logic layer
│   │   │   └── market_data.py # Async market data service
│   │   └── core/              # Core utilities
│   │       ├── financial_models.py # OOP financial classes
│   │       ├── utils.py       # Pandas analysis functions
│   │       └── config.py      # Application configuration
│   └── main.py                # FastAPI application entry
├── frontend/                  # Plotly Dash Frontend
│   ├── components/            # Reusable UI components
│   ├── layouts/              # Page layouts
│   └── app.py                # Main Dash application
├── data/                     # SQLite database storage
├── create_sample_data.py     # Sample data generator
├── test_integration.py       # API testing suite
└── requirements.txt          # Python dependencies
```

## 🛠️ Tech Stack

### Backend Technologies
- **FastAPI**: High-performance async web framework
- **SQLAlchemy**: Object-relational mapping and database management
- **Pandas & NumPy**: Financial data analysis and calculations
- **Async/Await**: Concurrent market data fetching
- **Pydantic**: Data validation and serialization
- **yfinance/Alpha Vantage**: Market data providers

### Frontend Technologies
- **Plotly Dash**: Interactive web applications in Python
- **Dash Bootstrap Components**: Professional UI components
- **Plotly Express/Graph Objects**: Advanced financial charting
- **Real-time Updates**: WebSocket-based data streaming

### Database & Storage
- **SQLite**: Lightweight relational database
- **Alembic**: Database migration management
- **JSON APIs**: RESTful data exchange

## 📦 Installation & Setup

### Quick Start (Recommended)

#### Windows:
```cmd
# Clone the repository
git clone <repository-url>
cd fpti

# Run the automated setup script
start.bat
```

#### Linux/macOS:
```bash
# Clone the repository
git clone <repository-url>
cd fpti

# Make script executable and run
chmod +x start.sh
./start.sh
```

### Manual Setup

1. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize Database**:
   ```bash
   python init_db.py
   ```

4. **Create Sample Data**:
   ```bash
   python create_sample_data.py
   ```

5. **Start Backend** (in one terminal):
   ```bash
   cd backend
   python main.py
   ```

6. **Start Frontend** (in another terminal):
   ```bash
   cd frontend
   python app.py
   ```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or run individual services
docker build -t fpti .
docker run -p 8000:8000 -p 8050:8050 fpti
```

## 🌐 Access Points

- **Frontend Dashboard**: http://localhost:8050
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## 📊 Usage Examples

### Portfolio Analysis
- Navigate to the **Dashboard** tab for portfolio overview
- View real-time portfolio values and daily changes
- Analyze asset allocation with interactive pie charts
- Monitor individual holdings performance

### Monte Carlo Simulations
- Go to **Monte Carlo** tab
- Set target retirement value and time horizon
- Adjust monthly contribution amounts
- Run simulations to see success probability

### Transaction Management
- Add new transactions via the **Transactions** tab
- Track buy/sell orders with automatic P&L calculation
- Monitor dividend payments and cash flows

### Market Data
- Real-time price updates every 5 minutes
- Historical price charts for technical analysis
- Market indices summary dashboard

## 🧪 Testing

Run the comprehensive test suite:
```bash
python test_integration.py
```

This will test:
- All API endpoints functionality
- Database connectivity
- Market data integration
- Frontend-backend communication

## 🔧 Configuration

### Environment Variables
Create a `.env` file based on `.env.example`:

```env
# Database
DATABASE_URL=sqlite:///./data/fpti.db

# Market Data APIs (optional for enhanced functionality)
ALPHA_VANTAGE_API_KEY=your_key_here
YAHOO_FINANCE_API_KEY=your_key_here

# Security
SECRET_KEY=your-secret-key-here

# Application Settings
DEBUG=True
API_V1_STR=/api/v1
```

### Market Data Providers
- **Default**: Yahoo Finance (free, no API key required)
- **Optional**: Alpha Vantage (requires free API key for enhanced features)

## 📈 Key Financial Metrics

The application calculates and displays:

- **Total Return**: Overall portfolio performance
- **Annualized Return**: Year-over-year growth rate
- **Volatility**: Risk measurement via standard deviation
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Value at Risk (VaR)**: Potential losses at 95% confidence
- **Beta**: Correlation with market movements

## 🎓 Educational Value

This project demonstrates:

1. **Full-Stack Development**: Complete application from database to UI
2. **Financial Mathematics**: Real-world quantitative finance implementation
3. **Async Programming**: Efficient concurrent data processing
4. **API Design**: RESTful services with automatic documentation
5. **Data Visualization**: Interactive financial charting
6. **Object-Oriented Design**: Clean, maintainable code architecture
7. **Database Design**: Normalized schema for financial data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Troubleshooting

### Common Issues:

1. **Port Already in Use**: Change ports in configuration files
2. **Database Errors**: Delete `data/fpti.db` and re-run `init_db.py`
3. **Market Data Failures**: Check internet connection and API keys
4. **Import Errors**: Ensure virtual environment is activated

### Getting Help:

- Check the test suite output: `python test_integration.py`
- Review API documentation at http://localhost:8000/docs
- Examine log files for detailed error messages

## 🔮 Future Enhancements

- Real-time WebSocket data streaming
- Advanced portfolio optimization algorithms
- Machine learning price prediction models
- Mobile-responsive design improvements
- Multi-user authentication system
- Integration with brokerage APIs
- Advanced risk management tools