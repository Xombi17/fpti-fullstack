"""
Main Dash application for the FPTI frontend.
"""
import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import json
import asyncio
import aiohttp
import os
from dotenv import load_dotenv
import yfinance as yf
from yahoo_finance_service import (
    fetch_yahoo_quote, 
    fetch_yahoo_intraday, 
    search_yahoo_symbols, 
    get_market_summary
)

# Load environment variables
load_dotenv()

# Constants for frequently used strings
TRANSPARENT_BG = 'rgba(0,0,0,0)'
FONT_FAMILY = 'Inter, sans-serif'
CHART_CONTAINER_SLIDE_UP = "chart-container slide-up"
CHART_CONTAINER_FADE_IN = "chart-container fade-in"
TEXT_MUTED_BLOCK = "text-muted d-block"
UNITED_STATES = "United States"
# Currency helper functions
def is_indian_stock(symbol: str) -> bool:
    """Check if a symbol is an Indian stock (NSE/BSE)."""
    return symbol.endswith('.NS') or symbol.endswith('.BO')

def format_currency(value: float, symbol: str) -> str:
    """Format currency based on stock origin."""
    if is_indian_stock(symbol):
        return f"{value:,.2f}"  # Indian rupees without symbol
    else:
        return f"${value:,.2f}"  # US dollars with symbol

def format_currency_compact(value: float, symbol: str) -> str:
    """Format currency in compact form."""
    if is_indian_stock(symbol):
        return f"{value:,.0f}"  # Indian rupees without symbol  
    else:
        return f"${value:,.0f}"  # US dollars with symbol

# Portfolio table columns
COL_AVG_COST = 'Avg Cost'
COL_CURRENT_PRICE = 'Current Price'
COL_MARKET_VALUE = 'Market Value'
COL_PL_PERCENT = 'P&L %'
COL_CHANGE_PERCENT = 'Change %'

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP, 
        dbc.icons.FONT_AWESOME,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
    ],
    suppress_callback_exceptions=True,
    assets_folder='assets'
)

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

# Market Data Functions - Yahoo Finance (No API key needed!)
# Yahoo Finance provides free real-time data with no rate limits
def fetch_live_market_data(symbols_list):
    """Fetch live market data for a list of symbols using Yahoo Finance."""
    quotes = []
    for symbol in symbols_list[:10]:  # Yahoo Finance has no rate limits, so we can fetch more
        try:
            quote_data = fetch_yahoo_quote(symbol)
            if quote_data:
                quotes.append({
                    "symbol": symbol,
                    "price": quote_data["price"],
                    "change": quote_data["change"],
                    "change_percent": quote_data["change_percent"],
                    "volume": quote_data["volume"],
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
    
    return {"quotes": quotes, "total": len(quotes)}

def fetch_detailed_quote(symbol):
    """Fetch detailed quote for a single symbol using Yahoo Finance."""
    try:
        # Try original symbol first
        quote_data = fetch_yahoo_quote(symbol)
        if quote_data and quote_data.get("price") is not None:
            print(f"DEBUG: Got Yahoo Finance data for {symbol}: {quote_data}")
            return quote_data
        
        # For Indian stocks, try adding .NS suffix if not present
        if not symbol.endswith('.NS') and not '.' in symbol:
            # Try with .NS suffix for Indian stocks
            symbol_ns = f"{symbol}.NS"
            print(f"DEBUG: Trying Indian stock symbol: {symbol_ns}")
            quote_data = fetch_yahoo_quote(symbol_ns)
            
            if quote_data and quote_data.get("price") is not None:
                print(f"DEBUG: Got Yahoo Finance data for {symbol_ns}: {quote_data}")
                return quote_data
        
        print(f"No data found for {symbol}, using mock data")
        return get_mock_quote_data(symbol)
    except Exception as e:
        print(f"Error fetching detailed quote for {symbol}: {e}")
        return get_mock_quote_data(symbol)

def get_mock_quote_data(symbol):
    """Return realistic mock data for demo purposes."""
    mock_data = {
        "AAPL": {
            "symbol": "AAPL",
            "open": 254.20,
            "high": 257.34,
            "low": 253.58,
            "price": 254.43,
            "volume": 60275187,
            "latest_trading_day": "2025-09-24",
            "previous_close": 256.08,
            "change": -1.65,
            "change_percent": "-0.64",
            "currency": "USD"
        },
        "GOOGL": {
            "symbol": "GOOGL",
            "open": 250.80,
            "high": 253.45,
            "low": 249.90,
            "price": 251.66,
            "volume": 1825000,
            "latest_trading_day": "2025-09-24",
            "previous_close": 252.10,
            "change": -0.44,
            "change_percent": "-0.17",
            "currency": "USD"
        },
        "MSFT": {
            "symbol": "MSFT",
            "open": 508.50,
            "high": 512.30,
            "low": 507.80,
            "price": 509.23,
            "volume": 18420000,
            "latest_trading_day": "2025-09-24",
            "previous_close": 507.90,
            "change": 1.33,
            "change_percent": "0.26",
            "currency": "USD"
        },
        # Indian stocks
        "RELIANCE.NS": {
            "symbol": "RELIANCE.NS",
            "open": 1381.30,
            "high": 1384.50,
            "low": 1369.00,
            "price": 1372.40,
            "volume": 11329904,
            "latest_trading_day": "2025-09-25",
            "previous_close": 1383.00,
            "change": -10.60,
            "change_percent": "-0.77",
            "currency": "INR"
        },
        "TCS.NS": {
            "symbol": "TCS.NS",
            "open": 3022.00,
            "high": 3029.60,
            "low": 2951.00,
            "price": 2957.40,
            "volume": 4971744,
            "latest_trading_day": "2025-09-25",
            "previous_close": 3035.40,
            "change": -78.00,
            "change_percent": "-2.57",
            "currency": "INR"
        },
        "INFY.NS": {
            "symbol": "INFY.NS",
            "open": 1489.00,
            "high": 1502.70,
            "low": 1476.50,
            "price": 1484.80,
            "volume": 9491460,
            "latest_trading_day": "2025-09-25",
            "previous_close": 1494.60,
            "change": -9.80,
            "change_percent": "-0.66",
            "currency": "INR"
        },
        # Common Indian stock names without .NS
        "RELIANCE": {
            "symbol": "RELIANCE.NS",
            "open": 1381.30,
            "high": 1384.50,
            "low": 1369.00,
            "price": 1372.40,
            "volume": 11329904,
            "latest_trading_day": "2025-09-25",
            "previous_close": 1383.00,
            "change": -10.60,
            "change_percent": "-0.77",
            "currency": "INR"
        },
        "TCS": {
            "symbol": "TCS.NS",
            "open": 3022.00,
            "high": 3029.60,
            "low": 2951.00,
            "price": 2957.40,
            "volume": 4971744,
            "latest_trading_day": "2025-09-25",
            "previous_close": 3035.40,
            "change": -78.00,
            "change_percent": "-2.57",
            "currency": "INR"
        },
        "INFY": {
            "symbol": "INFY.NS",
            "open": 1489.00,
            "high": 1502.70,
            "low": 1476.50,
            "price": 1484.80,
            "volume": 9491460,
            "latest_trading_day": "2025-09-25",
            "previous_close": 1494.60,
            "change": -9.80,
            "change_percent": "-0.66",
            "currency": "INR"
        }
    }
    
    # Return specific mock data if available, otherwise generic
    if symbol in mock_data:
        return mock_data[symbol]
    else:
        # Determine if it's an Indian stock for currency
        is_indian = symbol.endswith('.NS') or symbol.upper() in ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'SBI', 'BHARTIARTL', 'ICICIBANK', 'ITC', 'HINDUNILVR', 'KOTAKBANK', 'LT', 'ASIANPAINT', 'MARUTI', 'BAJFINANCE', 'HCLTECH', 'WIPRO', 'ULTRACEMCO', 'SBIN', 'AXISBANK', 'ONGC', 'SUNPHARMA', 'NESTLEIND', 'POWERGRID', 'NTPC', 'DRREDDY', 'JSWSTEEL', 'INDUSINDBK', 'ADANIPORTS', 'TECHM']
        
        if is_indian:
            return {
                "symbol": symbol,
                "open": 1500.00,
                "high": 1520.50,
                "low": 1485.20,
                "price": 1503.45,
                "volume": 5000000,
                "latest_trading_day": "2025-09-25",
                "previous_close": 1498.80,
                "change": 4.65,
                "change_percent": "0.31",
                "currency": "INR"
            }
        else:
            return {
                "symbol": symbol,
                "open": 100.00,
                "high": 105.50,
                "low": 99.20,
                "price": 103.45,
                "volume": 5000000,
                "latest_trading_day": "2025-09-24",
                "previous_close": 102.80,
                "change": 0.65,
                "change_percent": "0.63",
                "currency": "USD"
            }

# Mock data for portfolios and transactions
MOCK_PORTFOLIOS = [
    {"id": 1, "name": "Growth Portfolio"},
    {"id": 2, "name": "Dividend Portfolio"},
    {"id": 3, "name": "Tech Portfolio"}
]

# Global transaction storage - will persist during app session
MOCK_TRANSACTIONS = [
    {
        "id": 1,
        "portfolio_id": 1,
        "portfolio": {"name": "Growth Portfolio"},
        "asset": {"symbol": "AAPL"},
        "transaction_type": "BUY",
        "quantity": 50,
        "price": 175.25,
        "transaction_date": "2024-01-15T00:00:00"
    },
    {
        "id": 2,
        "portfolio_id": 1,
        "portfolio": {"name": "Growth Portfolio"},
        "asset": {"symbol": "GOOGL"},
        "transaction_type": "BUY",
        "quantity": 20,
        "price": 142.80,
        "transaction_date": "2024-01-20T00:00:00"
    },
    {
        "id": 3,
        "portfolio_id": 2,
        "portfolio": {"name": "Dividend Portfolio"},
        "asset": {"symbol": "RELIANCE"},
        "transaction_type": "BUY",
        "quantity": 100,
        "price": 2450.50,
        "transaction_date": "2024-02-01T00:00:00"
    },
    {
        "id": 4,
        "portfolio_id": 2,
        "portfolio": {"name": "Dividend Portfolio"},
        "asset": {"symbol": "TCS"},
        "transaction_type": "BUY",
        "quantity": 75,
        "price": 3850.75,
        "transaction_date": "2024-02-05T00:00:00"
    },
    {
        "id": 5,
        "portfolio_id": 3,
        "portfolio": {"name": "Tech Portfolio"},
        "asset": {"symbol": "MSFT"},
        "transaction_type": "BUY",
        "quantity": 30,
        "price": 420.60,
        "transaction_date": "2024-02-10T00:00:00"
    },
    {
        "id": 6,
        "portfolio_id": 1,
        "portfolio": {"name": "Growth Portfolio"},
        "asset": {"symbol": "AAPL"},
        "transaction_type": "SELL",
        "quantity": 10,
        "price": 185.40,
        "transaction_date": "2024-03-01T00:00:00"
    }
]

def fetch_intraday_data(symbol, interval="5min"):
    """Fetch intraday data for a symbol using Yahoo Finance."""
    try:
        # Map Alpha Vantage intervals to Yahoo Finance intervals
        interval_map = {
            "1min": "1m",
            "5min": "5m", 
            "15min": "15m",
            "30min": "30m",
            "60min": "1h"
        }
        
        yf_interval = interval_map.get(interval, "5m")
        intraday_data = fetch_yahoo_intraday(symbol, period="1d", interval=yf_interval)
        
        if intraday_data:
            return intraday_data
        else:
            print(f"No intraday data found for {symbol}, using mock data")
            return get_mock_intraday_data(symbol, interval)
            
    except Exception as e:
        print(f"Error fetching intraday data for {symbol}: {e}")
        return get_mock_intraday_data(symbol, interval)

def get_mock_intraday_data(symbol, interval="5min"):
    """Generate mock intraday data for demo purposes."""
    from datetime import datetime, timedelta
    import random
    
    base_price = 150.0  # Starting price
    data = []
    now = datetime.now()
    
    # Generate 50 data points going back in time
    for i in range(50, 0, -1):
        timestamp = (now - timedelta(minutes=i*5)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Simulate price movement
        price_change = random.uniform(-2, 2)
        base_price = max(base_price + price_change, base_price * 0.95)  # Don't let it drop too much
        
        open_price = base_price
        high_price = open_price + random.uniform(0, 3)
        low_price = open_price - random.uniform(0, 2)
        close_price = open_price + random.uniform(-1.5, 1.5)
        volume = random.randint(100000, 1000000)
        
        data.append({
            "timestamp": timestamp,
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": volume
        })
        
        base_price = close_price
    
    return {
        "symbol": symbol,
        "interval": interval,
        "data": data
    }

def fetch_market_summary():
    """Fetch market summary data using Yahoo Finance."""
    try:
        summary_data = get_market_summary()
        return {
            "indices": summary_data,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error fetching market summary: {e}")
        # Fallback to mock data
        return {
            "indices": {
                "S&P 500": 5745.37,
                "NASDAQ": 18291.62,
                "Dow Jones": 42063.36,
                "VIX": 16.85
            },
            "last_updated": datetime.now().isoformat()
        }

def fetch_asset_correlation_data(symbols, period="3mo"):
    """
    Fetch real asset correlation data using Yahoo Finance.
    Simple and reliable implementation.
    """
    try:
        print(f"DEBUG: Starting correlation fetch for {symbols}")
        
        # Handle single symbol case
        if len(symbols) <= 1:
            symbol = symbols[0] if symbols else 'AAPL'
            return pd.DataFrame([[1.0]], index=[symbol], columns=[symbol])
        
        # Use a simple approach - download each symbol individually
        price_data = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                if not hist.empty and 'Close' in hist.columns:
                    price_data[symbol] = hist['Close']
                    print(f"DEBUG: Successfully fetched {symbol}: {len(hist)} days")
                else:
                    print(f"DEBUG: No data for {symbol}")
            except Exception as e:
                print(f"DEBUG: Error fetching {symbol}: {e}")
                continue
        
        # Check if we have data for at least 2 symbols
        if len(price_data) < 2:
            print("DEBUG: Not enough symbols with data, using mock data")
            raise ValueError("Insufficient data for correlation")
        
        # Create DataFrame from individual symbol data
        df = pd.DataFrame(price_data)
        
        # Calculate returns
        returns = df.pct_change().dropna()
        
        if returns.empty or len(returns) < 5:  # Need at least 5 observations
            raise ValueError("Not enough return data for correlation")
        
        # Calculate correlation
        corr_matrix = returns.corr()
        
        # Fill any NaN values
        corr_matrix = corr_matrix.fillna(0)
        for i in range(len(corr_matrix)):
            corr_matrix.iloc[i, i] = 1.0  # Ensure diagonal is 1
        
        print(f"DEBUG: Successfully calculated correlation matrix {corr_matrix.shape}")
        return corr_matrix
        
    except Exception as e:
        print(f"DEBUG: Error in correlation calculation: {e}")
        # Return simple mock correlation matrix
        n = len(symbols)
        mock_values = np.eye(n)  # Identity matrix
        
        # Add some realistic correlations
        for i in range(n):
            for j in range(i+1, n):
                corr_val = np.random.uniform(0.2, 0.8)
                mock_values[i, j] = corr_val
                mock_values[j, i] = corr_val
        
        return pd.DataFrame(mock_values, index=symbols, columns=symbols)

def search_symbols(keywords):
    """Search for symbols using Yahoo Finance."""
    try:
        results = search_yahoo_symbols(keywords)
        if results:
            return results
        else:
            print(f"No search results found for '{keywords}', using mock data")
            return get_mock_search_results(keywords)
    except Exception as e:
        print(f"Error searching symbols for '{keywords}': {e}")
        return get_mock_search_results(keywords)

def get_mock_search_results(keywords):
    """Return mock search results as fallback."""
    if "apple" in keywords.lower():
        return [
            {
                "symbol": "AAPL",
                "name": "Apple Inc",
                "type": "Equity",
                "region": UNITED_STATES,
                "market_open": "09:30",
                "market_close": "16:00",
                "timezone": "UTC-04",
                "currency": "USD",
                "match_score": 1.0
            }
        ]
    elif "google" in keywords.lower():
        return [
            {
                "symbol": "GOOGL",
                "name": "Alphabet Inc Class A",
                "type": "Equity",
                "region": UNITED_STATES,
                "market_open": "09:30",
                "market_close": "16:00",
                "timezone": "UTC-04",
                "currency": "USD",
                "match_score": 1.0
            }
        ]
    else:
        return [
            {
                "symbol": keywords.upper(),
                "name": f"{keywords} Inc",
                "type": "Equity",
                "region": UNITED_STATES,
                "market_open": "09:30",
                "market_close": "16:00",
                "timezone": "UTC-04",
                "currency": "USD",
                "match_score": 0.8
            }
        ]

# App Layout
app.layout = dbc.Container([
    dcc.Store(id='portfolio-data-store'),
    dcc.Store(id='market-data-store'),
    dcc.Store(id='net-worth-assets-store', data=[
        {"type": "real_estate", "name": "Primary Home", "value": 37350000},
        {"type": "investment", "name": "Stock Portfolio", "value": 23240000},
        {"type": "cash", "name": "Savings Account", "value": 9960000}
    ]),
    dcc.Store(id='net-worth-liabilities-store', data=[
        {"type": "mortgage", "name": "Home Mortgage", "value": 26560000},
        {"type": "auto_loan", "name": "Car Loan", "value": 2075000}
    ]),
    dcc.Store(id='budgets-store', data=[
        {"category": "housing", "name": "Housing", "budget": 207500, "spent": 199200},
        {"category": "transportation", "name": "Transportation", "budget": 66400, "spent": 62250},
        {"category": "food", "name": "Food", "budget": 49800, "spent": 53950},
        {"category": "entertainment", "name": "Entertainment", "budget": 33200, "spent": 29050},
        {"category": "healthcare", "name": "Healthcare", "budget": 24900, "spent": 23240},
        {"category": "shopping", "name": "Shopping", "budget": 41500, "spent": 34860}
    ]),
    dcc.Interval(
        id='interval-component',
        interval=10*60*1000,  # Update every 10 minutes to respect API limits
        n_intervals=0
    ),
    
    # Modern Header
    html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("FPTI", className="mb-0"),
                    html.P("Financial Portfolio Tracking Interface", className="subtitle mb-0")
                ], className="text-center")
            ])
        ])
    ], className="modern-header"),
    
    # Professional Navigation Bar
    html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Nav([
                        dbc.NavItem(dbc.NavLink([
                            html.I(className="fas fa-chart-line me-2"),
                            "Dashboard"
                        ], href="#", id="nav-dashboard", className="nav-link-custom active", active=True)),
                        dbc.NavItem(dbc.NavLink([
                            html.I(className="fas fa-chart-pie me-2"),
                            "Analysis"
                        ], href="#", id="nav-analysis", className="nav-link-custom")),
                        dbc.NavItem(dbc.NavLink([
                            html.I(className="fas fa-exchange-alt me-2"),
                            "Transactions"
                        ], href="#", id="nav-transactions", className="nav-link-custom")),
                        dbc.NavItem(dbc.NavLink([
                            html.I(className="fas fa-dice me-2"),
                            "Monte Carlo"
                        ], href="#", id="nav-monte-carlo", className="nav-link-custom")),
                        dbc.NavItem(dbc.NavLink([
                            html.I(className="fas fa-chart-bar me-2"),
                            "Market Data"
                        ], href="#", id="nav-market-data", className="nav-link-custom")),
                        dbc.NavItem(dbc.NavLink([
                            html.I(className="fas fa-landmark me-2"),
                            "Net Worth"
                        ], href="#", id="nav-net-worth", className="nav-link-custom")),
                        dbc.NavItem(dbc.NavLink([
                            html.I(className="fas fa-wallet me-2"),
                            "Budgeting"
                        ], href="#", id="nav-budgeting", className="nav-link-custom")),
                    ], pills=True, className="nav-pills-custom justify-content-center")
                ])
            ])
        ])
    ], className="navigation-bar mb-4"),
    
    # Store for active tab
    dcc.Store(id='active-tab-store', data='dashboard'),
    
    # Page Title Section
    html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H2(id='page-title', className="page-title"),
                    html.P(id='page-subtitle', className="page-subtitle")
                ])
            ])
        ])
    ], className="page-header"),
    
    # Tab Content
    html.Div(id='tab-content'),
    
    # Error notifications
    html.Div(id='error-notifications', className="position-fixed", style={'top': '20px', 'right': '20px', 'zIndex': 9999})
    
], fluid=True)

# Dashboard Tab Content
def create_dashboard_layout():
    return [
        # Modern Portfolio Summary Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-wallet", style={"color": "#27ae60"})
                        ], className="metric-icon success"),
                        html.H4("Total Portfolio Value", className="card-title"),
                        html.H2(id="total-value", className="metric-value text-success"),
                        html.Div(id="total-pnl", className="metric-change")
                    ])
                ], className="modern-card success fade-in")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-chart-pie", style={"color": "#3498db"})
                        ], className="metric-icon info"),
                        html.H4("Number of Holdings", className="card-title"),
                        html.H2(id="total-holdings", className="metric-value text-info"),
                        html.Div("Active Positions", className="metric-change")
                    ])
                ], className="modern-card info fade-in")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-arrow-trend-up", style={"color": "#f39c12"})
                        ], className="metric-icon warning"),
                        html.H4("Today's Change", className="card-title"),
                        html.H2(id="daily-change", className="metric-value text-warning"),
                        html.Div(id="daily-change-percent", className="metric-change")
                    ])
                ], className="modern-card warning fade-in")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-trophy", style={"color": "#e74c3c"})
                        ], className="metric-icon primary"),
                        html.H4("Best Performer", className="card-title"),
                        html.H2(id="best-performer", className="metric-value text-success"),
                        html.Div(id="best-performer-change", className="metric-change")
                    ])
                ], className="modern-card fade-in")
            ], width=3),
        ], className="mb-4"),
        
        dbc.Row([
            # Portfolio Value Chart
            dbc.Col([
                html.Div([
                    html.H4("Portfolio Value Over Time", className="chart-title"),
                    dcc.Graph(id="portfolio-value-chart", config={'displayModeBar': False})
                ], className=CHART_CONTAINER_SLIDE_UP)
            ], width=8),
            
            # Asset Allocation Pie Chart
            dbc.Col([
                html.Div([
                    html.H4("Asset Allocation", className="chart-title"),
                    dcc.Graph(id="allocation-pie-chart", config={'displayModeBar': False})
                ], className=CHART_CONTAINER_SLIDE_UP)
            ], width=4),
        ], className="mb-4"),
        
        dbc.Row([
            # Holdings Table
            dbc.Col([
                html.Div([
                    html.H4("Current Holdings", className="chart-title"),
                    html.Div(id="holdings-table", className="modern-table")
                ], className=CHART_CONTAINER_SLIDE_UP)
            ])
        ])
    ]

# Portfolio Analysis Tab Content
def create_analysis_layout():
    return [
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4("Performance Metrics", className="chart-title"),
                    html.Div(id="performance-metrics")
                ], className=CHART_CONTAINER_FADE_IN)
            ], width=6),
            
            dbc.Col([
                html.Div([
                    html.H4("Risk Analysis", className="chart-title"),
                    html.Div(id="risk-metrics")
                ], className=CHART_CONTAINER_FADE_IN)
            ], width=6),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4("Sector Allocation", className="chart-title"),
                    dcc.Graph(id="sector-allocation-chart", config={'displayModeBar': False})
                ], className=CHART_CONTAINER_SLIDE_UP)
            ], width=6),
            
            dbc.Col([
                html.Div([
                    html.H4("Asset Correlation Matrix", className="chart-title"),
                    dcc.Graph(id="correlation-matrix", config={'displayModeBar': False})
                ], className=CHART_CONTAINER_SLIDE_UP)
            ], width=6),
        ])
    ]

# Transactions Tab Content
def create_transactions_layout():
    return [
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4("Add New Transaction", className="chart-title"),
                    dbc.Form([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Portfolio"),
                                dcc.Dropdown(
                                    id="trans-portfolio-dropdown",
                                    placeholder="Select Portfolio",
                                    className="modern-input"
                                )
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Asset Symbol"),
                                dbc.Input(
                                    id="trans-symbol-input",
                                    type="text",
                                    placeholder="e.g., AAPL",
                                    className="modern-input"
                                )
                            ], width=6),
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Transaction Type"),
                                dcc.Dropdown(
                                    id="trans-type-dropdown",
                                    options=[
                                        {"label": "Buy", "value": "BUY"},
                                        {"label": "Sell", "value": "SELL"}
                                    ],
                                    placeholder="Select Type",
                                    className="modern-input"
                                )
                            ], width=4),
                            dbc.Col([
                                dbc.Label("Quantity"),
                                dbc.Input(
                                    id="trans-quantity-input",
                                    type="number",
                                    min=0,
                                    step=0.01,
                                    className="modern-input"
                                )
                            ], width=4),
                            dbc.Col([
                                dbc.Label("Price per Share"),
                                dbc.Input(
                                    id="trans-price-input",
                                    type="number",
                                    min=0,
                                    step=0.01,
                                    className="modern-input"
                                )
                            ], width=4),
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Transaction Date"),
                                dcc.DatePickerSingle(
                                    id="trans-date-picker",
                                    date=datetime.now().date(),
                                    display_format="YYYY-MM-DD"
                                )
                            ], width=6),
                            dbc.Col([
                                html.Br(),
                                dbc.Button(
                                    "Add Transaction",
                                    id="add-transaction-btn",
                                    className="modern-button mt-2"
                                )
                            ], width=6),
                        ], className="mb-3"),
                    ])
                ], className="chart-container fade-in")
            ])
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4("Transaction History", className="chart-title"),
                    dbc.Row([
                        dbc.Col([
                            dcc.Dropdown(
                                id="trans-filter-portfolio",
                                placeholder="Filter by Portfolio",
                                className="modern-input mb-3"
                            )
                        ], width=4),
                        dbc.Col([
                            dcc.Dropdown(
                                id="trans-filter-type",
                                options=[
                                    {"label": "All", "value": "ALL"},
                                    {"label": "Buy", "value": "BUY"},
                                    {"label": "Sell", "value": "SELL"}
                                ],
                                value="ALL",
                                className="modern-input mb-3"
                            )
                        ], width=4),
                        dbc.Col([
                            dbc.Button(
                                "Refresh",
                                id="refresh-transactions-btn",
                                className="modern-button mb-3"
                            )
                        ], width=4),
                    ]),
                    html.Div(id="transactions-table", className="modern-table"),
                    html.Div(id="transaction-add-result", className="mt-3")
                ], className="chart-container slide-up")
            ])
        ])
    ]

# Market Data Tab Content
def create_market_data_layout():
    return [
        # Live Market Data Header
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.I(className="fas fa-broadcast-tower me-2"),
                    "Live Market Data powered by Alpha Vantage • Updates every 5 minutes"
                ], color="info", className="mb-4")
            ])
        ]),
        
        # Market Summary & Quote Lookup
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-chart-line me-2"),
                            "Market Summary"
                        ]),
                        html.Div(id="market-summary")
                    ])
                ], className="modern-card")
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-search-dollar me-2"),
                            "Stock Quote Lookup"
                        ]),
                        dbc.InputGroup([
                            dbc.Input(
                                id="stock-symbol-input",
                                placeholder="Enter symbol (e.g., AAPL)",
                                className="modern-input"
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-chart-bar me-2"), "Get Quote"],
                                id="get-quote-btn",
                                color="primary",
                                className="modern-button"
                            )
                        ], className="mb-3"),
                        html.Div(id="stock-quote-result")
                    ])
                ], className="modern-card")
            ], width=6),
        ], className="mb-4"),
        
        # Live Portfolio Updates & Symbol Search
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-coins me-2"),
                            "Live Portfolio Prices"
                        ]),
                        html.Div(id="live-portfolio-prices")
                    ])
                ], className="modern-card")
            ], width=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-search me-2"),
                            "Symbol Search"
                        ]),
                        dbc.InputGroup([
                            dbc.Input(
                                id="symbol-search-input",
                                placeholder="Search companies..."
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-search")],
                                id="symbol-search-btn",
                                color="info"
                            )
                        ], className="mb-3"),
                        html.Div(id="symbol-search-results", style={"max-height": "300px", "overflow-y": "auto"})
                    ])
                ], className="modern-card")
            ], width=4),
        ], className="mb-4"),
        
        # Intraday Chart
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-chart-area me-2"),
                            "Intraday Chart"
                        ]),
                        dbc.Row([
                            dbc.Col([
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="intraday-symbol-input",
                                        placeholder="Symbol",
                                        value="AAPL"
                                    ),
                                    dbc.Select(
                                        id="intraday-interval-select",
                                        options=[
                                            {"label": "1 minute", "value": "1min"},
                                            {"label": "5 minutes", "value": "5min"},
                                            {"label": "15 minutes", "value": "15min"},
                                            {"label": "30 minutes", "value": "30min"},
                                            {"label": "60 minutes", "value": "60min"}
                                        ],
                                        value="5min"
                                    ),
                                    dbc.Button(
                                        [html.I(className="fas fa-refresh me-2"), "Load"],
                                        id="load-intraday-btn",
                                        color="success"
                                    )
                                ])
                            ], width=6),
                            dbc.Col([
                                html.Small("Last updated: ", className="text-muted"),
                                html.Small(id="intraday-last-updated", className="text-muted")
                            ], width=6, className="d-flex align-items-center justify-content-end")
                        ], className="mb-3"),
                        dcc.Graph(id="intraday-chart")
                    ])
                ], className="modern-card")
            ])
        ])
    ]

# Monte Carlo Tab Content
def create_monte_carlo_layout():
    return [
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Monte Carlo Simulation Parameters"),
                        dbc.Form([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Target Value (₹ Crores)"),
                                    dbc.Input(
                                        id="mc-target-value",
                                        type="number",
                                        value=10,
                                        min=1,
                                        step=0.5,
                                        placeholder="10"
                                    ),
                                    html.Small("Enter value in crores (e.g., 10 = ₹10 crores)", className="text-muted")
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("Time Horizon (Years)"),
                                    dbc.Input(
                                        id="mc-years",
                                        type="number",
                                        value=15,
                                        min=1,
                                        max=50
                                    )
                                ], width=6),
                            ], className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Monthly SIP (₹)"),
                                    dbc.Input(
                                        id="mc-monthly-contribution",
                                        type="number",
                                        value=25000,
                                        min=0,
                                        step=1000,
                                        placeholder="25000"
                                    ),
                                    html.Small("Monthly investment amount", className="text-muted")
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("Number of Simulations"),
                                    dbc.Input(
                                        id="mc-simulations",
                                        type="number",
                                        value=1000,
                                        min=100,
                                        max=10000
                                    )
                                ], width=6),
                            ], className="mb-3"),
                            dbc.Button(
                                "Run Simulation",
                                id="run-monte-carlo",
                                color="primary",
                                className="mb-3"
                            )
                        ])
                    ])
                ])
            ], width=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Simulation Results"),
                        html.Div(id="monte-carlo-results")
                    ])
                ])
            ], width=8),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Simulation Distribution"),
                        dcc.Graph(id="monte-carlo-chart")
                    ])
                ])
            ])
        ])
    ]

# Net Worth Tab Content
def create_net_worth_layout():
    return [
        # Net Worth Summary Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-coins me-2"),
                            "Total Assets"
                        ]),
                        html.H2(id="total-assets", className="text-success mb-0"),
                        html.Small("Current market value", className="text-muted")
                    ])
                ], className="modern-card")
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-credit-card me-2"),
                            "Total Liabilities"
                        ]),
                        html.H2(id="total-liabilities", className="text-danger mb-0"),
                        html.Small("Outstanding debts", className="text-muted")
                    ])
                ], className="modern-card")
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-landmark me-2"),
                            "Net Worth"
                        ]),
                        html.H2(id="net-worth-total", className="text-primary mb-0"),
                        html.Small(id="net-worth-change", className="text-muted")
                    ])
                ], className="modern-card")
            ], width=4),
        ], className="mb-4"),
        
        # Net Worth Trend Chart
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-chart-line me-2"),
                            "Net Worth Trend"
                        ]),
                        dcc.Graph(id="net-worth-chart")
                    ])
                ], className="modern-card")
            ])
        ], className="mb-4"),
        
        # Assets and Liabilities Management
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-plus-circle me-2"),
                            "Add Asset"
                        ]),
                        dbc.Form([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Asset Type"),
                                    dbc.Select(
                                        id="asset-type-select",
                                        options=[
                                            {"label": "Cash", "value": "cash"},
                                            {"label": "Investment", "value": "investment"},
                                            {"label": "Real Estate", "value": "real_estate"},
                                            {"label": "Vehicle", "value": "vehicle"},
                                            {"label": "Personal Property", "value": "personal_property"},
                                            {"label": "Retirement Account", "value": "retirement_account"},
                                            {"label": "Business", "value": "business"},
                                            {"label": "Other", "value": "other"}
                                        ],
                                        className="modern-input"
                                    )
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("Asset Name"),
                                    dbc.Input(id="asset-name-input", placeholder="e.g., Checking Account")
                                ], width=6)
                            ], className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Current Value (₹)"),
                                    dbc.Input(id="asset-value-input", type="number", placeholder="0.00")
                                ], width=6),
                                dbc.Col([
                                    dbc.Button(
                                        [html.I(className="fas fa-plus me-2"), "Add Asset"],
                                        id="add-asset-btn",
                                        color="success",
                                        className="mt-4"
                                    )
                                ], width=6)
                            ])
                        ])
                    ])
                ], className="modern-card")
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-minus-circle me-2"),
                            "Add Liability"
                        ]),
                        dbc.Form([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Liability Type"),
                                    dbc.Select(
                                        id="liability-type-select",
                                        options=[
                                            {"label": "Mortgage", "value": "mortgage"},
                                            {"label": "Auto Loan", "value": "auto_loan"},
                                            {"label": "Student Loan", "value": "student_loan"},
                                            {"label": "Credit Card", "value": "credit_card"},
                                            {"label": "Personal Loan", "value": "personal_loan"},
                                            {"label": "Business Loan", "value": "business_loan"},
                                            {"label": "Other", "value": "other"}
                                        ],
                                        className="modern-input"
                                    )
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("Liability Name"),
                                    dbc.Input(id="liability-name-input", placeholder="e.g., Home Mortgage")
                                ], width=6)
                            ], className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Outstanding Balance (₹)"),
                                    dbc.Input(id="liability-balance-input", type="number", placeholder="0.00")
                                ], width=6),
                                dbc.Col([
                                    dbc.Button(
                                        [html.I(className="fas fa-plus me-2"), "Add Liability"],
                                        id="add-liability-btn",
                                        color="danger",
                                        className="mt-4"
                                    )
                                ], width=6)
                            ])
                        ])
                    ])
                ], className="modern-card")
            ], width=6)
        ], className="mb-4"),
        
        # Assets and Liabilities Tables
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-list me-2"),
                            "Assets"
                        ]),
                        html.Div(id="assets-table")
                    ])
                ], className="modern-card")
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-list me-2"),
                            "Liabilities"
                        ]),
                        html.Div(id="liabilities-table")
                    ])
                ], className="modern-card")
            ], width=6)
        ])
    ]

# Budgeting Tab Content
def create_budgeting_layout():
    return [
        # Budget Overview Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-dollar-sign me-2"),
                            "Monthly Income"
                        ]),
                        html.H2(id="monthly-income", className="text-success mb-0"),
                        html.Small("Total income this month", className="text-muted")
                    ])
                ], className="modern-card")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-shopping-cart me-2"),
                            "Total Spending"
                        ]),
                        html.H2(id="total-spending", className="text-danger mb-0"),
                        html.Small("Total expenses this month", className="text-muted")
                    ])
                ], className="modern-card")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-piggy-bank me-2"),
                            "Total Budget"
                        ]),
                        html.H2(id="total-budget", className="text-info mb-0"),
                        html.Small("Allocated budget this month", className="text-muted")
                    ])
                ], className="modern-card")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-chart-pie me-2"),
                            "Remaining"
                        ]),
                        html.H2(id="budget-remaining", className="text-primary mb-0"),
                        html.Small("Available budget", className="text-muted")
                    ])
                ], className="modern-card")
            ], width=3),
        ], className="mb-4"),
        
        # Budget Categories Chart
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-chart-donut me-2"),
                            "Budget vs Spending by Category"
                        ]),
                        dcc.Graph(id="budget-categories-chart")
                    ])
                ], className="modern-card")
            ], width=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-plus-circle me-2"),
                            "Create Budget"
                        ]),
                        dbc.Form([
                            dbc.Label("Budget Category"),
                            dbc.Select(
                                id="budget-category-select",
                                options=[
                                    {"label": "Housing", "value": "housing"},
                                    {"label": "Transportation", "value": "transportation"},
                                    {"label": "Food & Dining", "value": "food"},
                                    {"label": "Entertainment", "value": "entertainment"},
                                    {"label": "Healthcare", "value": "healthcare"},
                                    {"label": "Shopping", "value": "shopping"},
                                    {"label": "Utilities", "value": "utilities"},
                                    {"label": "Insurance", "value": "insurance"},
                                    {"label": "Education", "value": "education"},
                                    {"label": "Personal Care", "value": "personal_care"},
                                    {"label": "Travel", "value": "travel"},
                                    {"label": "Other", "value": "other"}
                                ],
                                className="modern-input mb-3"
                            ),
                            dbc.Label("Monthly Budget Amount (₹)"),
                            dbc.Input(
                                id="budget-amount-input",
                                type="number",
                                placeholder="0.00",
                                className="mb-3"
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-plus me-2"), "Create Budget"],
                                id="create-budget-btn",
                                color="primary",
                                className="w-100"
                            )
                        ])
                    ])
                ], className="modern-card")
            ], width=4)
        ], className="mb-4"),
        
        # Add Spending Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-shopping-cart me-2"),
                            "Add Spending"
                        ]),
                        dbc.Form([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Select Budget Category"),
                                    dbc.Select(
                                        id="spending-category-select",
                                        placeholder="Choose category...",
                                        className="modern-input"
                                    )
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("Amount Spent (₹)"),
                                    dbc.Input(
                                        id="spending-amount-input",
                                        type="number",
                                        placeholder="0.00"
                                    )
                                ], width=6)
                            ], className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Description"),
                                    dbc.Input(
                                        id="spending-description-input",
                                        placeholder="What did you spend on?"
                                    )
                                ], width=8),
                                dbc.Col([
                                    dbc.Button(
                                        [html.I(className="fas fa-plus me-2"), "Add Spending"],
                                        id="add-spending-btn",
                                        color="warning",
                                        className="mt-4 w-100"
                                    )
                                ], width=4)
                            ])
                        ])
                    ])
                ], className="modern-card")
            ])
        ], className="mb-4"),
        
        # Budget Progress Bars
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-tasks me-2"),
                            "Budget Progress"
                        ]),
                        html.Div(id="budget-progress-bars")
                    ])
                ], className="modern-card")
            ])
        ], className="mb-4"),
        
        # Recent Transactions
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4([
                            html.I(className="fas fa-history me-2"),
                            "Recent Transactions"
                        ]),
                        html.Div(id="recent-transactions-table")
                    ])
                ], className="modern-card")
            ])
        ])
    ]

# Navigation Click Handlers
@app.callback(
    [Output('active-tab-store', 'data'),
     Output('nav-dashboard', 'className'),
     Output('nav-analysis', 'className'),
     Output('nav-transactions', 'className'),
     Output('nav-monte-carlo', 'className'),
     Output('nav-market-data', 'className'),
     Output('nav-net-worth', 'className'),
     Output('nav-budgeting', 'className')],
    [Input('nav-dashboard', 'n_clicks'),
     Input('nav-analysis', 'n_clicks'),
     Input('nav-transactions', 'n_clicks'),
     Input('nav-monte-carlo', 'n_clicks'),
     Input('nav-market-data', 'n_clicks'),
     Input('nav-net-worth', 'n_clicks'),
     Input('nav-budgeting', 'n_clicks')],
    [State('active-tab-store', 'data')]
)
def update_navigation(dash_clicks, analysis_clicks, trans_clicks, mc_clicks, market_clicks, net_worth_clicks, budgeting_clicks, current_tab):
    ctx = dash.callback_context
    if not ctx.triggered:
        # Default state
        return 'dashboard', 'nav-link-custom active', 'nav-link-custom', 'nav-link-custom', 'nav-link-custom', 'nav-link-custom', 'nav-link-custom', 'nav-link-custom'
    
    # Determine which button was clicked
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Set active tab based on clicked button
    if button_id == 'nav-dashboard':
        active_tab = 'dashboard'
    elif button_id == 'nav-analysis':
        active_tab = 'analysis'
    elif button_id == 'nav-transactions':
        active_tab = 'transactions'
    elif button_id == 'nav-monte-carlo':
        active_tab = 'monte-carlo'
    elif button_id == 'nav-market-data':
        active_tab = 'market-data'
    elif button_id == 'nav-net-worth':
        active_tab = 'net-worth'
    elif button_id == 'nav-budgeting':
        active_tab = 'budgeting'
    else:
        active_tab = current_tab or 'dashboard'
    
    # Set className for each nav link
    classes = ['nav-link-custom'] * 7
    nav_mapping = {
        'dashboard': 0,
        'analysis': 1,
        'transactions': 2,
        'monte-carlo': 3,
        'market-data': 4,
        'net-worth': 5,
        'budgeting': 6
    }
    
    if active_tab in nav_mapping:
        classes[nav_mapping[active_tab]] = 'nav-link-custom active'
    
    return active_tab, *classes

# Page Title Callback
@app.callback(
    [Output('page-title', 'children'),
     Output('page-subtitle', 'children')],
    Input('active-tab-store', 'data')
)
def update_page_title(active_tab):
    titles = {
        'dashboard': ('Portfolio Dashboard', 'Real-time overview of your investment portfolio'),
        'analysis': ('Portfolio Analysis', 'In-depth performance and risk analysis'),
        'transactions': ('Transaction Management', 'Track and manage your investment transactions'),
        'monte-carlo': ('Monte Carlo Simulation', 'Advanced portfolio projections and scenarios'),
        'market-data': ('Market Data', 'Live market quotes and financial information'),
        'net-worth': ('Net Worth Tracking', 'Monitor your assets, liabilities, and overall financial position'),
        'budgeting': ('Budget Management', 'Create and track budgets to manage your spending')
    }
    
    title, subtitle = titles.get(active_tab, titles['dashboard'])
    return title, subtitle

# Tab Content Callback
@app.callback(
    Output('tab-content', 'children'),
    Input('active-tab-store', 'data')
)
def render_tab_content(active_tab):
    if active_tab == "dashboard":
        return create_dashboard_layout()
    elif active_tab == "analysis":
        return create_analysis_layout()
    elif active_tab == "monte-carlo":
        return create_monte_carlo_layout()
    elif active_tab == "transactions":
        return create_transactions_layout()
    elif active_tab == "market-data":
        return create_market_data_layout()
    elif active_tab == "net-worth":
        return create_net_worth_layout()
    elif active_tab == "budgeting":
        return create_budgeting_layout()
    return create_dashboard_layout()  # Default to dashboard

# Data Loading Callbacks
@app.callback(
    [Output('portfolio-data-store', 'data'),
     Output('market-data-store', 'data')],
    Input('interval-component', 'n_intervals')
)
def load_data(n):
    try:
        # Mock portfolio data for demo - Mixed Indian and US stocks
        portfolios = [{
            'id': 1,
            'name': 'My Portfolio',
            'holdings': [
                {'asset': {'symbol': 'RELIANCE.NS'}, 'quantity': 50},
                {'asset': {'symbol': 'TCS.NS'}, 'quantity': 25},
                {'asset': {'symbol': 'INFY.NS'}, 'quantity': 100},
                {'asset': {'symbol': 'AAPL'}, 'quantity': 10},
                {'asset': {'symbol': 'GOOGL'}, 'quantity': 5},
                {'asset': {'symbol': 'TSLA'}, 'quantity': 8}
            ]
        }]
        
        # Load market summary
        market_summary = fetch_market_summary()
        
        # Get portfolio symbols for live prices - Mixed stocks
        symbols = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'AAPL', 'GOOGL', 'TSLA']  # Mixed demo symbols
        
        # Fetch real live prices for portfolio symbols - Mixed stocks
        live_quotes = {}
        print(f"[DEBUG] Fetching live data for symbols: {symbols}")
        for symbol in symbols:
            try:
                quote_data = fetch_yahoo_quote(symbol)
                if quote_data:
                    print(f"[DEBUG] Got live data for {symbol}: {quote_data['price']}")
                    live_quotes[symbol] = {
                        'symbol': quote_data['symbol'],
                        'price': quote_data['price'],
                        'change': quote_data['change'],
                        'change_percent': quote_data['change_percent'],
                        'volume': quote_data['volume'],
                        'timestamp': datetime.now().isoformat(),
                        'currency': quote_data.get('currency', 'INR')
                    }
                else:
                    print(f"[DEBUG] No data received for {symbol}, using fallback")
                    # Fallback to mock data for failed fetches
                    fallback_data = {
                        'RELIANCE.NS': {'price': 1372.4, 'change': -22.75, 'change_percent': '-1.63'},
                        'TCS.NS': {'price': 2957.4, 'change': -25.80, 'change_percent': '-0.87'},
                        'INFY.NS': {'price': 1842.45, 'change': 18.65, 'change_percent': '1.02'},
                        'AAPL': {'price': 176.80, 'change': 1.50, 'change_percent': '0.86'},
                        'GOOGL': {'price': 2850.25, 'change': -15.30, 'change_percent': '-0.53'},
                        'TSLA': {'price': 248.50, 'change': 3.25, 'change_percent': '1.33'}
                    }
                    mock_data = fallback_data.get(symbol, {'price': 1000.0, 'change': 0.0, 'change_percent': '0.00'})
                    live_quotes[symbol] = {
                        'symbol': symbol,
                        'price': mock_data['price'],
                        'change': mock_data['change'],
                        'change_percent': mock_data['change_percent'],
                        'volume': 1000000,
                        'timestamp': datetime.now().isoformat(),
                        'currency': 'INR'
                    }
            except Exception as e:
                print(f"Error fetching live quote for {symbol}: {e}")
                # Fallback mock data
                live_quotes[symbol] = {
                    'symbol': symbol,
                    'price': 1000.0,
                    'change': 0.0,
                    'change_percent': '0.00',
                    'volume': 1000000,
                    'timestamp': datetime.now().isoformat(),
                    'currency': 'INR'
                }
        
        # Combine market data
        market_data = {
            'summary': market_summary,
            'live_quotes': live_quotes,
            'last_updated': datetime.now().isoformat()
        }
        
        return portfolios, market_data
    except Exception as e:
        print(f"Error loading data: {e}")
        return [], {}

# Dashboard Callbacks
@app.callback(
    [Output('total-value', 'children'),
     Output('total-pnl', 'children'),
     Output('total-holdings', 'children'),
     Output('daily-change', 'children'),
     Output('daily-change-percent', 'children'),
     Output('best-performer', 'children'),
     Output('best-performer-change', 'children')],
    Input('portfolio-data-store', 'data')
)
def update_dashboard_cards(portfolio_data):
    if not portfolio_data:
        return "₹0.00", "No P&L data", "0", "₹0.00", "0.00%", "N/A", "N/A"
    
    try:
        print("DEBUG: Updating dashboard with real portfolio data")
        
        # Calculate real values using Yahoo Finance data
        total_value_inr = 0
        total_holdings = 0
        daily_change_total = 0
        best_performer_symbol = ""
        best_performer_pct = -float('inf')
        
        # Demo portfolio with realistic quantities
        demo_holdings = [
            {'symbol': 'RELIANCE.NS', 'quantity': 50, 'avg_cost': 1350.0},
            {'symbol': 'TCS.NS', 'quantity': 25, 'avg_cost': 2900.0},
            {'symbol': 'INFY.NS', 'quantity': 100, 'avg_cost': 1400.0},
            {'symbol': 'AAPL', 'quantity': 10, 'avg_cost': 245.0},  # USD
            {'symbol': 'GOOGL', 'quantity': 5, 'avg_cost': 2800.0},  # USD
            {'symbol': 'TSLA', 'quantity': 8, 'avg_cost': 240.0}     # USD
        ]
        
        total_holdings = len(demo_holdings)
        
        # USD to INR conversion rate (approximate)
        usd_to_inr = 83.0
        
        for holding in demo_holdings:
            try:
                # Get real-time price
                quote_data = fetch_yahoo_quote(holding['symbol'])
                if quote_data:
                    current_price = quote_data['price']
                    quantity = holding['quantity']
                    avg_cost = holding['avg_cost']
                    
                    # Convert USD stocks to INR
                    if not is_indian_stock(holding['symbol']):
                        current_price_inr = current_price * usd_to_inr
                        avg_cost_inr = avg_cost * usd_to_inr
                    else:
                        current_price_inr = current_price
                        avg_cost_inr = avg_cost
                    
                    # Calculate position value and P&L
                    position_value = current_price_inr * quantity
                    position_cost = avg_cost_inr * quantity
                    position_pnl = position_value - position_cost
                    
                    total_value_inr += position_value
                    daily_change_total += position_pnl
                    
                    # Track best performer
                    pnl_pct = (position_pnl / position_cost) * 100 if position_cost > 0 else 0
                    if pnl_pct > best_performer_pct:
                        best_performer_pct = pnl_pct
                        best_performer_symbol = holding['symbol']
                        
                    print(f"DEBUG: {holding['symbol']}: ₹{current_price_inr:.2f} * {quantity} = ₹{position_value:,.2f} (P&L: {pnl_pct:.2f}%)")
                    
            except Exception as e:
                print(f"DEBUG: Error processing {holding['symbol']}: {e}")
                # Use fallback for this holding
                if is_indian_stock(holding['symbol']):
                    fallback_value = holding['avg_cost'] * holding['quantity']
                else:
                    fallback_value = holding['avg_cost'] * holding['quantity'] * usd_to_inr
                total_value_inr += fallback_value
        
        # Calculate percentages and format
        total_cost = sum(h['avg_cost'] * h['quantity'] * (usd_to_inr if not is_indian_stock(h['symbol']) else 1) for h in demo_holdings)
        total_pnl_pct = (daily_change_total / total_cost) * 100 if total_cost > 0 else 0
        daily_change_pct = abs(total_pnl_pct) * 0.1  # Assume 10% of total P&L is daily change
        
        # Format values
        total_value_str = f"₹{total_value_inr:,.0f}"
        total_pnl_str = f"₹{daily_change_total:,.0f} ({total_pnl_pct:+.2f}%)"
        total_holdings_str = str(total_holdings)
        daily_change_str = f"₹{daily_change_total * 0.1:,.0f}"  # 10% of total P&L as daily
        daily_change_percent_str = f"{daily_change_pct:+.2f}%"
        best_performer_str = best_performer_symbol.replace('.NS', '')  # Clean display
        best_performer_change_str = f"{best_performer_pct:+.2f}%"
        
        print(f"DEBUG: Total portfolio value: {total_value_str}")
        
        return total_value_str, total_pnl_str, total_holdings_str, daily_change_str, daily_change_percent_str, best_performer_str, best_performer_change_str
        
    except Exception as e:
        print(f"Error updating dashboard cards: {e}")
        import traceback
        traceback.print_exc()
        # Enhanced fallback with realistic Indian values
        return "₹15,45,230", "₹1,23,456 (+8.68%)", "6", "₹12,340", "+0.85%", "RELIANCE", "+2.45%"

@app.callback(
    Output('portfolio-value-chart', 'figure'),
    Input('portfolio-data-store', 'data')
)
def update_portfolio_chart(portfolio_data):
    try:
        print("DEBUG: Updating portfolio value chart with realistic data")
        
        # Generate realistic portfolio growth data based on market performance
        import random
        from datetime import datetime, timedelta
        
        # Create 6 months of daily data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Base portfolio value (in INR)
        base_value = 1400000  # ₹14 lakhs
        values = []
        
        # Simulate realistic portfolio growth with some volatility
        current_value = base_value
        for i, date in enumerate(dates):
            # Add trend growth (annual 12% = daily 0.032%)
            daily_growth = 0.00032
            
            # Add market volatility
            volatility = random.uniform(-0.025, 0.025)  # ±2.5% daily
            
            # Weekend effect (markets closed)
            if date.weekday() >= 5:  # Saturday/Sunday
                daily_change = daily_growth * 0.1  # Minimal change
            else:
                daily_change = daily_growth + volatility
            
            current_value = current_value * (1 + daily_change)
            values.append(current_value)
        
        print(f"DEBUG: Portfolio chart - Start: ₹{values[0]:,.0f}, End: ₹{values[-1]:,.0f}")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines',
            name='Portfolio Value',
            line={'color': '#0071f3', 'width': 3},
            fill='tonexty',
            fillcolor='rgba(0, 113, 243, 0.2)'
        ))
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Inter, sans-serif', 'color': '#e4e4e7'},
            xaxis={
                'title': {'text': 'Date', 'font': {'size': 14, 'color': '#a1a1aa'}},
                'showgrid': True,
                'gridcolor': 'rgba(161, 161, 170, 0.2)',
                'showline': False,
                'zeroline': False,
                'color': '#e4e4e7'
            },
            yaxis={
                'title': {'text': 'Portfolio Value', 'font': {'size': 14, 'color': '#a1a1aa'}},
                'showgrid': True,
                'gridcolor': 'rgba(161, 161, 170, 0.2)',
                'showline': False,
                'zeroline': False,
                'tickformat': ',.0f',
                'color': '#e4e4e7'
            },
            hovermode='x unified',
            showlegend=False,
            margin={'l': 40, 'r': 40, 't': 40, 'b': 40}
        )
        
        return fig
        
    except Exception as e:
        print(f"Error updating portfolio chart: {e}")
        # Return empty figure on error
        return go.Figure()

@app.callback(
    Output('allocation-pie-chart', 'figure'),
    Input('portfolio-data-store', 'data')
)
def update_allocation_chart(portfolio_data):
    try:
        print("DEBUG: Updating allocation chart with real portfolio data")
        
        # Calculate real allocation based on actual holdings
        demo_holdings = [
            {'symbol': 'RELIANCE.NS', 'quantity': 50, 'avg_cost': 1350.0, 'type': 'Indian Stocks'},
            {'symbol': 'TCS.NS', 'quantity': 25, 'avg_cost': 2900.0, 'type': 'Indian Stocks'},
            {'symbol': 'INFY.NS', 'quantity': 100, 'avg_cost': 1400.0, 'type': 'Indian Stocks'},
            {'symbol': 'AAPL', 'quantity': 10, 'avg_cost': 245.0, 'type': 'US Tech Stocks'},
            {'symbol': 'GOOGL', 'quantity': 5, 'avg_cost': 2800.0, 'type': 'US Tech Stocks'},
            {'symbol': 'TSLA', 'quantity': 8, 'avg_cost': 240.0, 'type': 'US Tech Stocks'}
        ]
        
        usd_to_inr = 83.0
        allocation_values = {}
        
        for holding in demo_holdings:
            try:
                quote_data = fetch_yahoo_quote(holding['symbol'])
                if quote_data:
                    current_price = quote_data['price']
                    if not is_indian_stock(holding['symbol']):
                        current_price_inr = current_price * usd_to_inr
                    else:
                        current_price_inr = current_price
                    
                    position_value = current_price_inr * holding['quantity']
                    asset_type = holding['type']
                    
                    if asset_type in allocation_values:
                        allocation_values[asset_type] += position_value
                    else:
                        allocation_values[asset_type] = position_value
                        
            except Exception as e:
                print(f"DEBUG: Error processing {holding['symbol']} for allocation: {e}")
                # Use avg cost as fallback
                fallback_price = holding['avg_cost']
                if not is_indian_stock(holding['symbol']):
                    fallback_price *= usd_to_inr
                fallback_value = fallback_price * holding['quantity']
                
                asset_type = holding['type']
                if asset_type in allocation_values:
                    allocation_values[asset_type] += fallback_value
                else:
                    allocation_values[asset_type] = fallback_value
        
        # Calculate percentages
        total_value = sum(allocation_values.values())
        asset_types = list(allocation_values.keys())
        values = list(allocation_values.values())
        percentages = [(v/total_value)*100 for v in values]
        
        print(f"DEBUG: Allocation - {dict(zip(asset_types, [f'{p:.1f}%' for p in percentages]))}")
        
        allocation_data = {
            'Asset Type': asset_types,
            'Percentage': percentages,
            'Value': values
        }
        
    except Exception as e:
        print(f"Error calculating real allocation: {e}")
        # Enhanced fallback allocation
        allocation_data = {
            'Asset Type': ['Indian Stocks', 'US Tech Stocks', 'Cash & Others'],
            'Percentage': [70, 25, 5],
            'Value': [1080000, 385000, 77000]
        }
    
    fig = px.pie(
        values=allocation_data['Percentage'],
        names=allocation_data['Asset Type'],
        color_discrete_sequence=[
            '#667eea', '#764ba2', '#f093fb', '#f5576c', 
            '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7'
        ]
    )
    
    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Value: %{value:,.0f}<br>Percentage: %{percent}<extra></extra>',
        textfont={'size': 12, 'color': 'white', 'family': 'Inter, sans-serif'}
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Inter, sans-serif', 'color': '#e4e4e7'},
        showlegend=True,
        legend={
            'orientation': 'v',
            'yanchor': 'middle',
            'y': 0.5,
            'xanchor': 'left',
            'x': 1.05,
            'font': {'color': '#e4e4e7'}
        },
        margin={'l': 20, 'r': 80, 't': 20, 'b': 20}
    )
    
    return fig

@app.callback(
    Output('holdings-table', 'children'),
    [Input('portfolio-data-store', 'data'),
     Input('market-data-store', 'data')]
)
def update_holdings_table(portfolio_data, market_data):
    try:
        print("DEBUG: Updating holdings table with real market data")
        
        # Demo portfolio with realistic values
        demo_holdings = [
            {'symbol': 'RELIANCE.NS', 'shares': 50, 'avg_cost': 1350.0},
            {'symbol': 'TCS.NS', 'shares': 25, 'avg_cost': 2900.0},
            {'symbol': 'INFY.NS', 'shares': 100, 'avg_cost': 1400.0},
            {'symbol': 'AAPL', 'shares': 10, 'avg_cost': 245.0},
            {'symbol': 'GOOGL', 'shares': 5, 'avg_cost': 2800.0},
            {'symbol': 'TSLA', 'shares': 8, 'avg_cost': 240.0}
        ]
        
        holdings_data = {
            'Symbol': [],
            'Shares': [],
            'Avg Cost': [],
            'Current Price': [],
            'Market Value': [],
            'P&L': [],
            'P&L %': []
        }
        
        usd_to_inr = 83.0
        
        for holding in demo_holdings:
            symbol = holding['symbol']
            shares = holding['shares']
            avg_cost = holding['avg_cost']
            
            try:
                # Get real current price from Yahoo Finance
                quote_data = fetch_yahoo_quote(symbol)
                if quote_data:
                    current_price = quote_data['price']
                    print(f"DEBUG: {symbol}: Live price ₹{current_price}")
                else:
                    # Fallback if Yahoo Finance fails
                    fallback_prices = {
                        'RELIANCE.NS': 1372.4, 'TCS.NS': 2957.4, 'INFY.NS': 1484.8,
                        'AAPL': 252.52, 'GOOGL': 2850.25, 'TSLA': 248.50
                    }
                    current_price = fallback_prices.get(symbol, avg_cost)
                    print(f"DEBUG: {symbol}: Using fallback price ₹{current_price}")
                
            except Exception as e:
                print(f"DEBUG: Error fetching {symbol}: {e}")
                current_price = avg_cost  # Use avg cost as last resort
            
            # Convert prices for display (everything in INR for consistency)
            if is_indian_stock(symbol):
                display_avg_cost = avg_cost
                display_current_price = current_price
                display_symbol = symbol.replace('.NS', '')  # Clean display
            else:
                # Convert USD to INR for display
                display_avg_cost = avg_cost * usd_to_inr
                display_current_price = current_price * usd_to_inr
                display_symbol = f"{symbol} (USD)"
            
            # Calculate values
            market_value = display_current_price * shares
            cost_basis = display_avg_cost * shares
            pnl = market_value - cost_basis
            pnl_percent = (pnl / cost_basis * 100) if cost_basis > 0 else 0
            
            holdings_data['Symbol'].append(display_symbol)
            holdings_data['Shares'].append(shares)
            holdings_data['Avg Cost'].append(display_avg_cost)
            holdings_data['Current Price'].append(display_current_price)
            holdings_data['Market Value'].append(market_value)
            holdings_data['P&L'].append(pnl)
            holdings_data['P&L %'].append(pnl_percent)
        
        df = pd.DataFrame(holdings_data)
        
    except Exception as e:
        print(f"Error creating holdings table: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to basic mock data
        holdings_data = {
            'Symbol': ['RELIANCE', 'TCS', 'INFY'],
            'Shares': [50, 25, 100],
            'Avg Cost': [1350.0, 2900.0, 1400.0],
            'Current Price': [1372.4, 2957.4, 1484.8],
            'Market Value': [68620, 73935, 148480],
            'P&L': [1120, 1435, 8480],
            'P&L %': [1.66, 1.98, 6.06]
        }
        df = pd.DataFrame(holdings_data)
    
    # Format currency columns and store original P&L for conditional styling
    pnl_values = []
    if not df.empty and 'P&L' in df.columns:
        for idx, row in df.iterrows():
            pnl_values.append(row['P&L'])
            # Format all monetary values as INR (no symbol, just numbers)
            df.at[idx, 'Avg Cost'] = f"₹{row['Avg Cost']:,.0f}"
            df.at[idx, 'Current Price'] = f"₹{row['Current Price']:,.0f}"
            df.at[idx, 'Market Value'] = f"₹{row['Market Value']:,.0f}"
            df.at[idx, 'P&L'] = f"₹{row['P&L']:,.0f}"
            df.at[idx, 'P&L %'] = f"{row['P&L %']:+.2f}%"
    
    return dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[
            {'name': 'Symbol', 'id': 'Symbol'},
            {'name': 'Shares', 'id': 'Shares', 'type': 'numeric'},
            {'name': 'Avg Cost', 'id': 'Avg Cost'},
            {'name': 'Current Price', 'id': 'Current Price'},
            {'name': 'Market Value', 'id': 'Market Value'},
            {'name': 'P&L', 'id': 'P&L'},
            {'name': 'P&L %', 'id': 'P&L %'},
        ],
        style_cell={
            'textAlign': 'center',
            'fontFamily': 'Inter, sans-serif',
            'fontSize': '14px',
            'padding': '10px'
        },
        style_header={
            'backgroundColor': '#374151',
            'color': 'white',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'row_index': i},
                'backgroundColor': '#d1fae5' if pnl_val >= 0 else '#fee2e2',
                'color': '#065f46' if pnl_val >= 0 else '#991b1b'
            } for i, pnl_val in enumerate(pnl_values)
        ] if pnl_values else []
    )

# Monte Carlo Callback
@app.callback(
    [Output('monte-carlo-results', 'children'),
     Output('monte-carlo-chart', 'figure')],
    [Input('run-monte-carlo', 'n_clicks')],
    [Input('mc-target-value', 'value'),
     Input('mc-years', 'value'),
     Input('mc-monthly-contribution', 'value'),
     Input('mc-simulations', 'value')]
)
def run_monte_carlo_simulation(n_clicks, target_value, years, monthly_contribution, num_simulations):
    if not n_clicks:
        return "Click 'Run Simulation' to see results", {}
    
    try:
        # Set default values - all inputs are already in rupees
        target_value = (target_value or 10) * 10000000  # Convert crores to rupees (10 crores = 100 million INR)
        years = years or 15
        monthly_contribution = monthly_contribution or 25000  # Already in rupees
        num_simulations = num_simulations or 1000
        
        # Run Monte Carlo simulation locally
        import numpy as np
        rng = np.random.default_rng(42)
        
        # Simulation parameters
        initial_portfolio_value = 500000  # 5 lakh rupees starting portfolio (more realistic)
        annual_return_mean = 0.12  # 12% average annual return (Indian markets)
        annual_return_std = 0.18   # 18% volatility
        
        # Run simulations
        final_values = []
        
        for _ in range(num_simulations):
            portfolio_value = initial_portfolio_value
            
            for year in range(years):
                # Annual return with volatility
                annual_return = rng.normal(annual_return_mean, annual_return_std)
                portfolio_value = portfolio_value * (1 + annual_return)
                
                # Add monthly contributions throughout the year
                portfolio_value += monthly_contribution * 12
            
            final_values.append(portfolio_value)
        
        final_values = np.array(final_values)
        
        # Calculate statistics
        percentiles = {
            '5th': np.percentile(final_values, 5),
            '25th': np.percentile(final_values, 25),
            '50th': np.percentile(final_values, 50),
            '75th': np.percentile(final_values, 75),
            '95th': np.percentile(final_values, 95)
        }
        
        success_probability = np.sum(final_values >= target_value) / num_simulations
        
        # Create results summary
        results_summary = [
            dbc.Alert([
                html.H5(f"Success Probability: {success_probability:.1%}"),
                html.P(f"Chance of reaching ₹{target_value:,.0f} in {years} years")
            ], color="success" if success_probability > 0.5 else "warning"),
            
            html.H6("Projected Values:"),
            html.Ul([
                html.Li(f"5th percentile: ₹{percentiles['5th']:,.0f}"),
                html.Li(f"25th percentile: ₹{percentiles['25th']:,.0f}"),
                html.Li(f"Median (50th): ₹{percentiles['50th']:,.0f}"),
                html.Li(f"75th percentile: ₹{percentiles['75th']:,.0f}"),
                html.Li(f"95th percentile: ₹{percentiles['95th']:,.0f}"),
            ]),
            
            html.Hr(),
            html.H6("Simulation Parameters:"),
            html.Ul([
                html.Li(f"Initial Portfolio: ₹{initial_portfolio_value:,.0f}"),
                html.Li(f"Monthly Contribution: ₹{monthly_contribution:,.0f}"),
                html.Li(f"Expected Annual Return: {annual_return_mean:.1%}"),
                html.Li(f"Volatility: {annual_return_std:.1%}"),
                html.Li(f"Time Horizon: {years} years"),
                html.Li(f"Simulations Run: {num_simulations:,}")
            ])
        ]
        
        # Create histogram chart
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=final_values,
            nbinsx=50,
            name='Simulation Results',
            marker={'color': '#667eea', 'opacity': 0.7},
            hovertemplate='Value Range: ₹%{x:,.0f}<br>Count: %{y}<extra></extra>'
        ))
        
        fig.add_vline(
            x=target_value, 
            line={'dash': "dash", 'color': "#e74c3c", 'width': 3},
            annotation={'text': f"Target: ₹{target_value/10000000:.1f}Cr", 'font': {'color': '#e74c3c', 'size': 12}}
        )
        
        fig.add_vline(
            x=percentiles['50th'], 
            line={'dash': "dot", 'color': "#2ecc71", 'width': 2},
            annotation={'text': f"Median: ₹{percentiles['50th']/10000000:.1f}Cr", 'font': {'color': '#2ecc71', 'size': 10}}
        )
        
        fig.update_layout(
            title=f"Monte Carlo Simulation Results ({num_simulations:,} simulations)",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Inter, sans-serif', 'color': '#e4e4e7'},
            xaxis_title="Portfolio Value (₹)",
            yaxis_title="Frequency",
            showlegend=False
        )
        
        return results_summary, fig
        
    except Exception as e:
        error_msg = f"Error running simulation: {str(e)}"
        return dbc.Alert(error_msg, color="danger"), {}

# Transactions Callbacks
@app.callback(
    [Output('trans-portfolio-dropdown', 'options'),
     Output('trans-filter-portfolio', 'options')],
    Input('interval-component', 'n_intervals')
)
def update_portfolio_dropdowns(n):
    try:
        # Use mock portfolios instead of API call
        options = [{"label": p["name"], "value": p["id"]} for p in MOCK_PORTFOLIOS]
        return options, [{"label": "All", "value": "ALL"}] + options
    except Exception as e:
        print(f"Error loading portfolios: {e}")
        return [], [{"label": "All", "value": "ALL"}]

@app.callback(
    Output('transaction-add-result', 'children'),
    [Input('add-transaction-btn', 'n_clicks')],
    [State('trans-portfolio-dropdown', 'value'),
     State('trans-symbol-input', 'value'),
     State('trans-type-dropdown', 'value'),
     State('trans-quantity-input', 'value'),
     State('trans-price-input', 'value'),
     State('trans-date-picker', 'date')]
)
def add_transaction(n_clicks, portfolio_id, symbol, trans_type, quantity, price, date):
    if not n_clicks or not all([portfolio_id, symbol, trans_type, quantity, price, date]):
        return ""
    
    try:
        # Find portfolio name
        portfolio_name = "Unknown"
        for p in MOCK_PORTFOLIOS:
            if p["id"] == portfolio_id:
                portfolio_name = p["name"]
                break
        
        # Add transaction to mock data
        new_transaction = {
            "id": len(MOCK_TRANSACTIONS) + 1,
            "portfolio_id": portfolio_id,
            "portfolio": {"name": portfolio_name},
            "asset": {"symbol": symbol.upper()},
            "transaction_type": trans_type,
            "quantity": float(quantity),
            "price": float(price),
            "transaction_date": f"{date}T00:00:00"
        }
        
        MOCK_TRANSACTIONS.append(new_transaction)
        return dbc.Alert("Transaction added successfully!", color="success", dismissable=True)
    
    except Exception as e:
        return dbc.Alert(f"Error: {str(e)}", color="danger", dismissable=True)

@app.callback(
    Output('transactions-table', 'children'),
    [Input('refresh-transactions-btn', 'n_clicks'),
     Input('trans-filter-portfolio', 'value'),
     Input('trans-filter-type', 'value'),
     Input('transaction-add-result', 'children')]
)
def update_transactions_table(n_clicks, portfolio_filter, type_filter, add_result):
    try:
        # Use mock transactions instead of API call
        transactions = MOCK_TRANSACTIONS
        if not transactions:
            return html.P("No transactions found")
        
        # Filter transactions
        filtered_transactions = transactions
        if portfolio_filter and portfolio_filter != "ALL":
            filtered_transactions = [t for t in filtered_transactions if t["portfolio_id"] == portfolio_filter]
        if type_filter and type_filter != "ALL":
            filtered_transactions = [t for t in filtered_transactions if t["transaction_type"] == type_filter]
        
        # Convert to DataFrame
        df_data = []
        for trans in filtered_transactions:
            df_data.append({
                "Date": trans["transaction_date"][:10],
                "Portfolio": trans.get("portfolio", {}).get("name", "Unknown"),
                "Symbol": trans.get("asset", {}).get("symbol", "Unknown"),
                "Type": trans["transaction_type"],
                "Quantity": trans["quantity"],
                "Price": trans["price"],
                "Total": trans["quantity"] * trans["price"]
            })
        
        if not df_data:
            return html.P("No transactions match the filters")
        
        df = pd.DataFrame(df_data)
        
        return dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[
                {"name": "Date", "id": "Date"},
                {"name": "Portfolio", "id": "Portfolio"},
                {"name": "Symbol", "id": "Symbol"},
                {"name": "Type", "id": "Type"},
                {"name": "Quantity", "id": "Quantity", "type": "numeric"},
                {"name": "Price", "id": "Price", "type": "numeric", "format": {"specifier": ",.2f"}},
                {"name": "Total", "id": "Total", "type": "numeric", "format": {"specifier": ",.2f"}},
            ],
            style_cell={'textAlign': 'center'},
            style_data_conditional=[
                {
                    'if': {'filter_query': '{Type} = BUY'},
                    'backgroundColor': '#d4edda',
                    'color': 'black',
                },
                {
                    'if': {'filter_query': '{Type} = SELL'},
                    'backgroundColor': '#f8d7da',
                    'color': 'black',
                }
            ],
            sort_action="native",
            page_size=10
        )
        
    except Exception as e:
        return html.P(f"Error loading transactions: {str(e)}")

# Portfolio Analysis Helper Functions
def calculate_portfolio_holdings():
    """Calculate current portfolio holdings from transactions."""
    holdings = {}
    
    for transaction in MOCK_TRANSACTIONS:
        symbol = transaction['asset']['symbol']
        quantity = transaction['quantity']
        
        if symbol not in holdings:
            holdings[symbol] = 0
        
        if transaction['transaction_type'] == 'BUY':
            holdings[symbol] += quantity
        elif transaction['transaction_type'] == 'SELL':
            holdings[symbol] -= quantity
    
    # Remove symbols with zero holdings
    holdings = {symbol: qty for symbol, qty in holdings.items() if qty > 0}
    return holdings

def calculate_portfolio_value():
    """Calculate total portfolio value using current holdings and live prices."""
    holdings = calculate_portfolio_holdings()
    total_value = 0
    portfolio_details = []
    
    for symbol, quantity in holdings.items():
        try:
            # Convert Indian stock names to proper Yahoo format
            yahoo_symbol = symbol
            if symbol in ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK']:
                yahoo_symbol = f"{symbol}.NS"
            
            # Get current price using the enhanced fetch function
            quote_data = fetch_yahoo_quote(yahoo_symbol)
            if quote_data:
                current_price = quote_data['price']
                currency = quote_data.get('currency', 'USD')
                
                # Convert to INR if needed
                if currency == 'USD':
                    current_price_inr = current_price * 83  # USD to INR conversion
                else:
                    current_price_inr = current_price
                
                holding_value = quantity * current_price_inr
                total_value += holding_value
                
                portfolio_details.append({
                    'symbol': symbol,
                    'quantity': quantity,
                    'current_price': current_price,
                    'current_price_inr': current_price_inr,
                    'value': holding_value,
                    'currency': currency
                })
        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
    
    return total_value, portfolio_details

def calculate_portfolio_performance():
    """Calculate portfolio performance metrics."""
    try:
        holdings = calculate_portfolio_holdings()
        total_invested = 0
        current_value, portfolio_details = calculate_portfolio_value()
        
        # Calculate total invested amount from transactions
        for transaction in MOCK_TRANSACTIONS:
            symbol = transaction['asset']['symbol']
            if symbol in holdings:  # Only count if we still hold the stock
                if transaction['transaction_type'] == 'BUY':
                    total_invested += transaction['quantity'] * transaction['price']
                elif transaction['transaction_type'] == 'SELL':
                    total_invested -= transaction['quantity'] * transaction['price']
        
        if total_invested > 0:
            total_return = ((current_value - total_invested) / total_invested) * 100
            
            # Simple annualized return (assuming 1 year holding period)
            annualized_return = total_return  # Simplified for demo
            
            # Mock volatility and other metrics for now
            volatility = 15.5  # Would calculate from historical data
            risk_free_rate = 4.0  # Current risk-free rate
            sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0
            
            return {
                'total_return': round(total_return, 2),
                'annualized_return': round(annualized_return, 2),
                'volatility': volatility,
                'sharpe_ratio': round(sharpe_ratio, 2),
                'max_drawdown': -8.5,  # Mock for now
                'beta': 0.95,  # Mock for now
                'total_invested': total_invested,
                'current_value': current_value
            }
    except Exception as e:
        print(f"Error calculating performance: {e}")
    
    return None

def get_sector_mapping():
    """Map stock symbols to sectors."""
    return {
        'AAPL': 'Technology',
        'GOOGL': 'Technology', 
        'MSFT': 'Technology',
        'TSLA': 'Consumer Discretionary',
        'NVDA': 'Technology',
        'RELIANCE': 'Energy',
        'RELIANCE.NS': 'Energy',
        'TCS': 'Technology',
        'TCS.NS': 'Technology',
        'INFY': 'Technology',
        'INFY.NS': 'Technology',
        'HDFC': 'Financial Services',
        'HDFC.NS': 'Financial Services',
        'ICICIBANK': 'Financial Services',
        'ICICIBANK.NS': 'Financial Services'
    }

def calculate_sector_allocation():
    """Calculate sector allocation based on current holdings."""
    holdings = calculate_portfolio_holdings()
    _, portfolio_details = calculate_portfolio_value()
    sector_mapping = get_sector_mapping()
    
    sector_values = {}
    total_value = sum(detail['value'] for detail in portfolio_details)
    
    for detail in portfolio_details:
        symbol = detail['symbol']
        sector = sector_mapping.get(symbol, 'Other')
        
        if sector not in sector_values:
            sector_values[sector] = 0
        sector_values[sector] += detail['value']
    
    # Convert to percentages
    if total_value > 0:
        sector_percentages = {
            sector: round((value / total_value) * 100, 1)
            for sector, value in sector_values.items()
        }
        return sector_percentages
    
    return {}

# Portfolio Analysis Callbacks
@app.callback(
    Output('performance-metrics', 'children'),
    Input('portfolio-data-store', 'data')
)
def update_performance_metrics(portfolio_data):
    try:
        if not portfolio_data:
            return html.P("No portfolio data available")
        
        # Calculate real performance metrics
        performance = calculate_portfolio_performance()
        
        if performance:
            metrics = [
                {
                    "metric": "Total Return", 
                    "value": f"{performance['total_return']:.1f}%", 
                    "color": "success" if performance['total_return'] > 0 else "danger"
                },
                {
                    "metric": "Annualized Return", 
                    "value": f"{performance['annualized_return']:.1f}%", 
                    "color": "success" if performance['annualized_return'] > 0 else "danger"
                },
                {
                    "metric": "Volatility", 
                    "value": f"{performance['volatility']:.1f}%", 
                    "color": "warning"
                },
                {
                    "metric": "Sharpe Ratio", 
                    "value": f"{performance['sharpe_ratio']:.2f}", 
                    "color": "info" if performance['sharpe_ratio'] > 1 else "secondary"
                },
                {
                    "metric": "Max Drawdown", 
                    "value": f"{performance['max_drawdown']:.1f}%", 
                    "color": "danger"
                },
                {
                    "metric": "Beta", 
                    "value": f"{performance['beta']:.2f}", 
                    "color": "secondary"
                }
            ]
        else:
            # Fallback metrics if calculation fails
            metrics = [
                {"metric": "Total Return", "value": "N/A", "color": "secondary"},
                {"metric": "Annualized Return", "value": "N/A", "color": "secondary"},
                {"metric": "Volatility", "value": "N/A", "color": "secondary"},
                {"metric": "Sharpe Ratio", "value": "N/A", "color": "secondary"},
                {"metric": "Max Drawdown", "value": "N/A", "color": "secondary"},
                {"metric": "Beta", "value": "N/A", "color": "secondary"}
            ]
        
        cards = []
        for metric in metrics:
            cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6(metric["metric"], className="card-title"),
                            html.H4(metric["value"], className=f"text-{metric['color']}")
                        ])
                    ])
                ], width=6, className="mb-3")
            )
        
        return dbc.Row(cards)
        
    except Exception as e:
        return html.P(f"Error loading performance metrics: {str(e)}")

@app.callback(
    Output('risk-metrics', 'children'),
    Input('portfolio-data-store', 'data')
)
def update_risk_metrics(portfolio_data):
    try:
        if not portfolio_data:
            return html.P("No portfolio data available")
        
        # Calculate real risk metrics
        current_value, portfolio_details = calculate_portfolio_value()
        holdings = calculate_portfolio_holdings()
        
        # Calculate concentration risk
        if portfolio_details:
            max_position = max(detail['value'] for detail in portfolio_details)
            concentration_pct = (max_position / current_value) * 100 if current_value > 0 else 0
            
            if concentration_pct > 40:
                concentration_risk = ("High", "danger")
            elif concentration_pct > 25:
                concentration_risk = ("Medium", "warning") 
            else:
                concentration_risk = ("Low", "success")
        else:
            concentration_risk = ("N/A", "secondary")
        
        # Simple VaR calculation (2% of portfolio value)
        var_95 = current_value * 0.02 if current_value > 0 else 0
        
        # Count liquid vs illiquid holdings (assume all stocks are liquid for now)
        liquid_count = len([h for h in holdings.keys() if not h.endswith('.NS')])  # US stocks are more liquid
        total_count = len(holdings)
        liquidity_score = "High" if liquid_count / total_count > 0.5 else "Medium" if liquid_count > 0 else "Low"
        liquidity_color = "success" if liquidity_score == "High" else "warning" if liquidity_score == "Medium" else "danger"
        
        risk_metrics = [
            {
                "metric": "Value at Risk (95%)", 
                "value": f"₹{var_95:,.0f}", 
                "color": "danger"
            },
            {
                "metric": "Expected Shortfall", 
                "value": f"₹{var_95 * 1.5:,.0f}", 
                "color": "danger"
            },
            {
                "metric": "Concentration Risk", 
                "value": concentration_risk[0], 
                "color": concentration_risk[1]
            },
            {
                "metric": "Liquidity Score", 
                "value": liquidity_score, 
                "color": liquidity_color
            },
            {
                "metric": "Portfolio Diversity", 
                "value": f"{len(holdings)} assets", 
                "color": "info"
            },
            {
                "metric": "Largest Position", 
                "value": f"{concentration_pct:.1f}%", 
                "color": "secondary"
            }
        ]
        
        cards = []
        for metric in risk_metrics:
            cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6(metric["metric"], className="card-title"),
                            html.H4(metric["value"], className=f"text-{metric['color']}")
                        ])
                    ])
                ], width=6, className="mb-3")
            )
        
        return dbc.Row(cards)
        
    except Exception as e:
        return html.P(f"Error loading risk metrics: {str(e)}")

@app.callback(
    Output('sector-allocation-chart', 'figure'),
    Input('portfolio-data-store', 'data')
)
def update_sector_allocation(portfolio_data):
    try:
        # Calculate real sector allocation from current holdings
        sector_percentages = calculate_sector_allocation()
        
        if not sector_percentages:
            # Fallback if no data
            sectors = ['No Data']
            values = [100]
        else:
            sectors = list(sector_percentages.keys())
            values = list(sector_percentages.values())
        
        fig = px.pie(
            values=values,
            names=sectors,
            color_discrete_sequence=[
                '#667eea', '#764ba2', '#f093fb', '#f5576c', '#4ecdc4'
            ]
        )
        
        fig.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Allocation: %{value}%<br>Percentage: %{percent}<extra></extra>',
            textfont={'size': 11, 'color': 'white', 'family': 'Inter, sans-serif'}
        )
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Inter, sans-serif', 'color': '#e4e4e7'},
            showlegend=True,
            legend={
                'orientation': 'v',
                'yanchor': 'middle',
                'y': 0.5,
                'xanchor': 'left',
                'x': 1.05
            },
            margin={'l': 20, 'r': 80, 't': 20, 'b': 20}
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creating sector allocation chart: {e}")
        return {}

@app.callback(
    Output('correlation-matrix', 'figure'),
    Input('portfolio-data-store', 'data')
)
def update_correlation_matrix(portfolio_data):
    print("DEBUG: update_correlation_matrix called")
    
    # Always return a working correlation matrix
    try:
        # Use real portfolio holdings
        holdings = calculate_portfolio_holdings()
        assets = list(holdings.keys())[:6]  # Limit to 6 assets for better visualization
        
        if not assets:
            # Fallback to some basic assets if no holdings
            assets = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        
        print(f"DEBUG: Creating correlation matrix for portfolio holdings: {assets}")
        
        # Create correlation data directly in callback to avoid function call issues
        correlation_data = []
        price_data = {}
        
        # Fetch data for each symbol
        for symbol in assets:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1mo")
                if not hist.empty and 'Close' in hist.columns:
                    price_data[symbol] = hist['Close']
                    print(f"DEBUG: Got data for {symbol}")
            except Exception as e:
                print(f"DEBUG: Error with {symbol}: {e}")
                continue
        
        # If we have enough data, calculate real correlations
        if len(price_data) >= 2:
            df = pd.DataFrame(price_data)
            returns = df.pct_change().dropna()
            if len(returns) >= 5:
                corr_matrix = returns.corr()
                corr_matrix = corr_matrix.fillna(0)
                np.fill_diagonal(corr_matrix.values, 1)
                print(f"DEBUG: Real correlation matrix calculated")
            else:
                # Fallback to mock data
                corr_matrix = create_mock_correlation(assets)
                print(f"DEBUG: Using mock correlation - insufficient returns")
        else:
            # Fallback to mock data
            corr_matrix = create_mock_correlation(assets)
            print(f"DEBUG: Using mock correlation - insufficient symbols")
        
        print(f"DEBUG: Final correlation matrix shape: {corr_matrix.shape}")
        
        # Create the visualization
        fig = px.imshow(
            corr_matrix.values,
            x=corr_matrix.columns.tolist(),
            y=corr_matrix.index.tolist(),
            color_continuous_scale='RdBu_r',
            aspect="auto",
            text_auto='.2f',
            zmin=-1,
            zmax=1
        )
        
        # Style the plot
        fig.update_layout(
            title={
                'text': "Asset Correlation Matrix (1 month)",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16, 'color': '#e4e4e7'}
            },
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Inter, sans-serif', 'color': '#e4e4e7'},
            xaxis={'side': 'bottom', 'showgrid': False, 'tickangle': 45},
            yaxis={'showgrid': False},
            margin={'l': 60, 'r': 60, 't': 60, 'b': 80},
            coloraxis_colorbar={
                'title': 'Correlation',
                'tickmode': 'linear',
                'tick0': -1,
                'dtick': 0.5
            }
        )
        
        fig.update_traces(
            hovertemplate='<b>%{x} vs %{y}</b><br>Correlation: %{z:.3f}<br><extra></extra>',
            textfont={'size': 10, 'family': 'Inter, sans-serif', 'color': 'white'}
        )
        
        print("DEBUG: Successfully created correlation figure")
        return fig
        
    except Exception as e:
        print(f"DEBUG: Error in correlation callback: {e}")
        import traceback
        traceback.print_exc()
        
        # Return a simple fallback figure
        fig = go.Figure()
        fig.add_annotation(
            text=f"Debug: Correlation callback error - {str(e)[:50]}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font={'size': 12, 'color': '#e4e4e7'}
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis={'visible': False},
            yaxis={'visible': False}
        )
        return fig

def create_mock_correlation(symbols):
    """Create a mock correlation matrix for fallback"""
    n = len(symbols)
    mock_values = np.eye(n)
    
    # Add realistic correlations
    correlations = {
        ('AAPL', 'GOOGL'): 0.35,
        ('AAPL', 'MSFT'): 0.25,
        ('AAPL', 'TSLA'): 0.40,
        ('GOOGL', 'MSFT'): 0.15,
        ('GOOGL', 'TSLA'): 0.10,
        ('MSFT', 'TSLA'): 0.20
    }
    
    for i, sym1 in enumerate(symbols):
        for j, sym2 in enumerate(symbols):
            if i != j:
                key = (sym1, sym2) if (sym1, sym2) in correlations else (sym2, sym1)
                if key in correlations:
                    mock_values[i, j] = correlations[key]
                else:
                    mock_values[i, j] = np.random.uniform(0.1, 0.3)
    
    return pd.DataFrame(mock_values, index=symbols, columns=symbols)

# Global Error Handling
@app.callback(
    Output('error-notifications', 'children'),
    [Input('portfolio-data-store', 'data'),
     Input('market-data-store', 'data')],
    prevent_initial_call=True
)
def show_connection_errors(portfolio_data, market_data):
    """Show error notifications for connection issues"""
    alerts = []
    
    # Check if we have connection issues
    if not portfolio_data and not market_data:
        alerts.append(
            dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Unable to connect to backend API. Please ensure the server is running on port 8000."
            ], color="warning", dismissable=True, duration=10000)
        )
    elif not portfolio_data:
        alerts.append(
            dbc.Alert([
                html.I(className="fas fa-database me-2"),
                "No portfolio data available. Add some portfolios and transactions to get started."
            ], color="info", dismissable=True, duration=8000)
        )
    
    return alerts

# Market Data Callbacks
@app.callback(
    Output('market-summary', 'children'),
    Input('market-data-store', 'data')
)
def update_market_summary(market_data):
    try:
        if not market_data or 'summary' not in market_data:
            return html.P("No market data available", className="text-muted")
        
        summary = market_data['summary']
        if not summary or 'indices' not in summary:
            return html.P("Market summary unavailable", className="text-muted")
        
        indices = summary['indices']
        cards = []
        
        for name, price in indices.items():
            if price is not None:
                cards.append(
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6(name, className="card-title text-muted"),
                                html.H5(f"{price:,.2f}", className="text-info mb-0"),
                                html.Small("Live", className="text-success")
                            ])
                        ], className="text-center")
                    ], width=6, className="mb-2")
                )
        
        return dbc.Row(cards) if cards else html.P("No data available", className="text-muted")
    except Exception as e:
        return html.P(f"Error: {str(e)}", className="text-danger")

@app.callback(
    Output('stock-quote-result', 'children'),
    [Input('get-quote-btn', 'n_clicks')],
    [State('stock-symbol-input', 'value')]
)
def get_stock_quote(n_clicks, symbol):
    if not n_clicks or not symbol:
        return ""
    
    print(f"DEBUG: get_stock_quote called with symbol: {symbol}")
    symbol_upper = symbol.upper()
    print(f"DEBUG: Calling fetch_detailed_quote with: {symbol_upper}")
    
    quote_data = fetch_detailed_quote(symbol_upper)
    print(f"DEBUG: fetch_detailed_quote returned: {quote_data}")
    
    if not quote_data:
        return dbc.Alert("Quote not found or API error", color="danger")
    
    change_color = "success" if quote_data['change'] >= 0 else "danger"
    change_icon = "fa-arrow-up" if quote_data['change'] >= 0 else "fa-arrow-down"
    
    symbol = quote_data['symbol']
    
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H4(quote_data['symbol'], className="mb-1"),
                    html.H3(format_currency(quote_data['price'], symbol), className="text-primary mb-0")
                ], width=6),
                dbc.Col([
                    html.P([
                        html.I(className=f"fas {change_icon} me-1"),
                        f"{format_currency(quote_data['change'], symbol)} ({quote_data['change_percent']}%)"
                    ], className=f"text-{change_color} mb-1"),
                    html.Small(f"Volume: {quote_data['volume']:,}", className="text-muted")
                ], width=6, className="text-end")
            ]),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.Small("Open", className="text-muted d-block"),
                    html.Strong(format_currency(quote_data['open'], symbol))
                ], width=3),
                dbc.Col([
                    html.Small("High", className="text-muted d-block"),
                    html.Strong(format_currency(quote_data['high'], symbol))
                ], width=3),
                dbc.Col([
                    html.Small("Low", className="text-muted d-block"),
                    html.Strong(format_currency(quote_data['low'], symbol))
                ], width=3),
                dbc.Col([
                    html.Small("Prev Close", className="text-muted d-block"),
                    html.Strong(format_currency(quote_data['previous_close'], symbol))
                ], width=3)
            ])
        ])
    ])

@app.callback(
    Output('live-portfolio-prices', 'children'),
    Input('market-data-store', 'data')
)
def update_live_portfolio_prices(market_data):
    try:
        if not market_data or 'live_quotes' not in market_data:
            return html.P("No live data available", className="text-muted")
        
        live_quotes = market_data['live_quotes']
        if not live_quotes:
            return html.P("No portfolio symbols found", className="text-muted")
        
        table_data = []
        for symbol, quote in live_quotes.items():
            table_data.append({
                "Symbol": symbol,
                "Price": format_currency(quote['price'], symbol),
                "Change": format_currency(quote['change'], symbol),
                "Change %": f"{quote['change_percent']}%",
                "Volume": f"{quote['volume']:,}",
                "Status": "LIVE"
            })
        
        if not table_data:
            return html.P("No live quotes available", className="text-muted")
        
        return dash_table.DataTable(
            data=table_data,
            columns=[
                {"name": "Symbol", "id": "Symbol"},
                {"name": "Price", "id": "Price"},
                {"name": "Change", "id": "Change"},
                {"name": "Change %", "id": "Change %"},
                {"name": "Volume", "id": "Volume"},
                {"name": "Status", "id": "Status"}
            ],
            style_cell={'textAlign': 'left', 'fontSize': '14px'},
            style_data_conditional=[
                {
                    'if': {'filter_query': '{Change} > 0'},
                    'color': '#00d084'
                },
                {
                    'if': {'filter_query': '{Change} < 0'},
                    'color': '#ff4757'
                }
            ],
            style_header={'backgroundColor': 'var(--dark-surface)', 'color': 'var(--light-text)'},
            style_cell_conditional=[
                {'if': {'column_id': 'Status'}, 'color': '#00d084', 'fontWeight': 'bold'}
            ]
        )
    except Exception as e:
        return html.P(f"Error: {str(e)}", className="text-danger")

@app.callback(
    Output('symbol-search-results', 'children'),
    [Input('symbol-search-btn', 'n_clicks')],
    [State('symbol-search-input', 'value')]
)
def search_symbols_callback(n_clicks, keywords):
    if not n_clicks or not keywords:
        return ""
    
    search_results = search_symbols(keywords)
    if not search_results:
        return dbc.Alert("No symbols found or API error", color="warning")
    
    results = []
    for result in search_results[:10]:  # Limit to top 10 results
        results.append(
            dbc.ListGroupItem([
                html.Div([
                    html.Strong(result['symbol'], className="text-primary"),
                    html.Small(f" • {result['region']} • {result['currency']}", className="text-muted ms-2")
                ]),
                html.Small(result['name'], className="text-muted"),
                html.Small(f"Match: {result['match_score']:.1%}", className="text-info float-end")
            ])
        )
    
    return dbc.ListGroup(results)

@app.callback(
    [Output('intraday-chart', 'figure'),
     Output('intraday-last-updated', 'children')],
    [Input('load-intraday-btn', 'n_clicks')],
    [State('intraday-symbol-input', 'value'),
     State('intraday-interval-select', 'value')]
)
def update_intraday_chart(n_clicks, symbol, interval):
    if not n_clicks or not symbol:
        # Return a default chart with sample data instead of empty
        fig = go.Figure()
        fig.add_annotation(
            text="Enter a stock symbol and click Load to view intraday chart",
            x=0.5, y=0.5, 
            showarrow=False,
            font=dict(size=16, color='#94a3b8')
        )
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Inter, sans-serif', 'color': '#e4e4e7'},
            height=400
        )
        return fig, ""
    
    print(f"DEBUG: Intraday chart requested for {symbol} with interval {interval}")
    
    # Convert symbol to uppercase and handle Indian stocks
    symbol_upper = symbol.upper()
    
    # For common Indian stock names, try .NS suffix if not present
    if not symbol_upper.endswith('.NS') and not '.' in symbol_upper:
        common_indian_stocks = ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'SBI', 'BHARTIARTL', 'ICICIBANK']
        if symbol_upper in common_indian_stocks:
            symbol_upper = f"{symbol_upper}.NS"
            print(f"DEBUG: Converted to Indian stock symbol: {symbol_upper}")
    
    intraday_data = fetch_intraday_data(symbol_upper, interval)
    print(f"DEBUG: Intraday data received: {intraday_data}")
    
    if not intraday_data or 'data' not in intraday_data:
        print(f"DEBUG: No valid intraday data found. Data keys: {intraday_data.keys() if intraday_data else 'None'}")
        fig = go.Figure()
        fig.add_annotation(text="No intraday data available", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        return fig, "Error loading data"
    
    df_data = pd.DataFrame(intraday_data['data'])
    df_data['timestamp'] = pd.to_datetime(df_data['timestamp'])
    df_data = df_data.sort_values('timestamp')
    
    fig = go.Figure()
    
    # Add candlestick chart
    fig.add_trace(go.Candlestick(
        x=df_data['timestamp'],
        open=df_data['open'],
        high=df_data['high'],
        low=df_data['low'],
        close=df_data['close'],
        name=symbol.upper()
    ))
    
    # Determine currency label based on symbol
    currency_symbol = "₹" if symbol_upper.endswith('.NS') or symbol_upper.endswith('.BO') else "$"
    
    fig.update_layout(
        title=f"{symbol_upper} - {interval} Intraday Chart",
        xaxis_title="Time",
        yaxis_title=f"Price ({currency_symbol})",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Inter, sans-serif', 'color': '#e4e4e7'},
        xaxis_rangeslider_visible=False
    )
    
    return fig, datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Net Worth Callbacks
@app.callback(
    [Output('total-assets', 'children'),
     Output('total-liabilities', 'children'),
     Output('net-worth-total', 'children'),
     Output('net-worth-change', 'children')],
    [Input('net-worth-assets-store', 'data'),
     Input('net-worth-liabilities-store', 'data')]
)
def update_net_worth_summary(assets_data, liabilities_data):
    """Update net worth summary cards with real data."""
    try:
        # Calculate totals from actual data
        total_assets = sum(asset['value'] for asset in assets_data) if assets_data else 0
        total_liabilities = sum(liability['value'] for liability in liabilities_data) if liabilities_data else 0
        net_worth = total_assets - total_liabilities
        
        # Calculate change (simplified - in real app would compare to previous period)
        change_percent = 2.5 if net_worth > 0 else 0
        
        return (
            f"₹{total_assets:,.0f}",
            f"₹{total_liabilities:,.0f}",
            f"₹{net_worth:,.0f}",
            f"↗ +{change_percent}% this month" if net_worth > 0 else "No change"
        )
    except Exception as e:
        return "₹0", "₹0", "₹0", "No data"

@app.callback(
    Output('net-worth-chart', 'figure'),
    [Input('net-worth-assets-store', 'data'),
     Input('net-worth-liabilities-store', 'data')]
)
def update_net_worth_chart(assets_data, liabilities_data):
    """Update net worth trend chart based on current data."""
    try:
        # Calculate current net worth
        current_assets = sum(asset['value'] for asset in assets_data) if assets_data else 0
        current_liabilities = sum(liability['value'] for liability in liabilities_data) if liabilities_data else 0
        current_net_worth = current_assets - current_liabilities
        
        # Generate historical trend based on current net worth
        dates = pd.date_range(start='2024-01-01', end='2025-09-25', freq='M')
        
        # Create a trend that leads to current net worth
        growth_rate = 0.02  # 2% monthly growth
        trend = []
        for i, date in enumerate(dates):
            if i == len(dates) - 1:  # Last point is current net worth
                trend.append(current_net_worth)
            else:
                # Work backwards from current value
                months_back = len(dates) - 1 - i
                past_value = current_net_worth / ((1 + growth_rate) ** months_back)
                # Add some randomness
                variation = np.random.uniform(-0.05, 0.05) * past_value
                trend.append(max(0, past_value + variation))
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=trend,
            mode='lines+markers',
            name='Net Worth',
            line=dict(color='#667eea', width=3),
            marker=dict(size=6),
            hovertemplate='<b>%{x|%B %Y}</b><br>Net Worth: ₹%{y:,.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Net Worth Trend",
            xaxis_title="Date",
            yaxis_title="Net Worth (₹)",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Inter, sans-serif', 'color': '#e4e4e7'},
            showlegend=False
        )
        
        return fig
    except Exception as e:
        return {}

@app.callback(
    [Output('assets-table', 'children'),
     Output('asset-name-input', 'value'),
     Output('asset-value-input', 'value'),
     Output('asset-type-select', 'value'),
     Output('net-worth-assets-store', 'data')],
    [Input('add-asset-btn', 'n_clicks')],
    [State('asset-type-select', 'value'),
     State('asset-name-input', 'value'),
     State('asset-value-input', 'value'),
     State('net-worth-assets-store', 'data')]
)
def handle_add_asset(n_clicks, asset_type, asset_name, asset_value, current_assets):
    """Handle adding new assets and update store."""
    assets_data = current_assets or []
    
    # Add new asset if form was submitted
    if n_clicks and asset_type and asset_name and asset_value:
        try:
            new_asset = {
                "type": asset_type,
                "name": asset_name,
                "value": float(asset_value)
            }
            assets_data.append(new_asset)
        except (ValueError, TypeError):
            pass  # Invalid input, don't add
    
    # Create display table
    display_data = []
    for asset in assets_data:
        display_data.append({
            "Type": asset['type'].title().replace('_', ' '),
            "Name": asset['name'],
            "Value": f"₹{asset['value']:,.0f}"
        })
    
    table = dbc.Table.from_dataframe(
        pd.DataFrame(display_data),
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        className="mb-0"
    ) if display_data else html.P("No assets added yet.", className="text-muted")
    
    # Clear form if asset was added
    if n_clicks and asset_type and asset_name and asset_value:
        return table, "", "", None, assets_data
    
    return table, dash.no_update, dash.no_update, dash.no_update, assets_data

@app.callback(
    [Output('liabilities-table', 'children'),
     Output('liability-name-input', 'value'),
     Output('liability-balance-input', 'value'),
     Output('liability-type-select', 'value'),
     Output('net-worth-liabilities-store', 'data')],
    [Input('add-liability-btn', 'n_clicks')],
    [State('liability-type-select', 'value'),
     State('liability-name-input', 'value'),
     State('liability-balance-input', 'value'),
     State('net-worth-liabilities-store', 'data')]
)
def handle_add_liability(n_clicks, liability_type, liability_name, liability_balance, current_liabilities):
    """Handle adding new liabilities and update store."""
    liabilities_data = current_liabilities or []
    
    # Add new liability if form was submitted
    if n_clicks and liability_type and liability_name and liability_balance:
        try:
            new_liability = {
                "type": liability_type,
                "name": liability_name,
                "value": float(liability_balance)
            }
            liabilities_data.append(new_liability)
        except (ValueError, TypeError):
            pass  # Invalid input, don't add
    
    # Create display table
    display_data = []
    for liability in liabilities_data:
        display_data.append({
            "Type": liability['type'].title().replace('_', ' '),
            "Name": liability['name'],
            "Balance": f"₹{liability['value']:,.0f}"
        })
    
    table = dbc.Table.from_dataframe(
        pd.DataFrame(display_data),
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        className="mb-0"
    ) if display_data else html.P("No liabilities added yet.", className="text-muted")
    
    # Clear form if liability was added
    if n_clicks and liability_type and liability_name and liability_balance:
        return table, "", "", None, liabilities_data
    
    return table, dash.no_update, dash.no_update, dash.no_update, liabilities_data


# Budgeting Callbacks
@app.callback(
    [Output('monthly-income', 'children'),
     Output('total-spending', 'children'),
     Output('total-budget', 'children'),
     Output('budget-remaining', 'children')],
    Input('budgets-store', 'data')
)
def update_budget_summary(budgets_data):
    """Update budget summary cards with real data."""
    try:
        if not budgets_data:
            return "₹0", "₹0", "₹0", "₹0"
        
        # Calculate totals from actual budget data
        total_budget = sum(budget['budget'] for budget in budgets_data)
        total_spending = sum(budget['spent'] for budget in budgets_data)
        monthly_income = total_budget * 1.15  # Assume income is 15% more than budget
        remaining = total_budget - total_spending
        
        return (
            f"₹{monthly_income:,.0f}",
            f"₹{total_spending:,.0f}",
            f"₹{total_budget:,.0f}",
            f"₹{remaining:,.0f}"
        )
    except Exception as e:
        return "₹0", "₹0", "₹0", "₹0"

@app.callback(
    Output('budget-categories-chart', 'figure'),
    Input('budgets-store', 'data')
)
def update_budget_chart(budgets_data):
    """Update budget vs spending chart with real data."""
    try:
        if not budgets_data:
            return {}
        
        # Extract data from budget store
        categories = [budget['name'] for budget in budgets_data]
        budgets = [budget['budget'] for budget in budgets_data]
        spending = [budget['spent'] for budget in budgets_data]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Budget',
            x=categories,
            y=budgets,
            marker_color='#667eea',
            hovertemplate='<b>%{x}</b><br>Budget: ₹%{y:,.0f}<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            name='Spent',
            x=categories,
            y=spending,
            marker_color='#f5576c',
            hovertemplate='<b>%{x}</b><br>Spent: ₹%{y:,.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Budget vs Spending by Category",
            xaxis_title="Category",
            yaxis_title="Amount (₹)",
            barmode='group',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Inter, sans-serif', 'color': '#e4e4e7'}
        )
        
        return fig
    except Exception as e:
        return {}

@app.callback(
    [Output('budget-progress-bars', 'children'),
     Output('budget-category-select', 'value'),
     Output('budget-amount-input', 'value'),
     Output('budgets-store', 'data')],
    [Input('create-budget-btn', 'n_clicks')],
    [State('budget-category-select', 'value'),
     State('budget-amount-input', 'value'),
     State('budgets-store', 'data')]
)
def handle_create_budget(n_clicks, category, amount, current_budgets):
    """Handle creating new budgets and update progress bars."""
    budget_data = current_budgets or []
    
    # Add new budget if form was submitted
    if n_clicks and category and amount:
        try:
            # Check if budget already exists for this category
            existing_budget = next((b for b in budget_data if b['category'] == category), None)
            if existing_budget:
                # Update existing budget
                existing_budget['budget'] = float(amount)
                existing_budget['name'] = category.title().replace('_', ' ')
            else:
                # Add new budget
                new_budget = {
                    "category": category,
                    "name": category.title().replace('_', ' '),
                    "budget": float(amount),
                    "spent": 0  # Start with 0 spending
                }
                budget_data.append(new_budget)
        except (ValueError, TypeError):
            pass  # Invalid input, don't add
    
    # Create progress bars from current data
    progress_bars = []
    for budget in budget_data:
        percentage = (budget['spent'] / budget['budget'] * 100) if budget['budget'] > 0 else 0
        color = "success" if percentage <= 80 else "warning" if percentage <= 100 else "danger"
        
        progress_bars.append(
            dbc.Row([
                dbc.Col([
                    html.H6(f"{budget['name']}", className="mb-1"),
                    html.Small(f"₹{budget['spent']:,.0f} of ₹{budget['budget']:,.0f}", className="text-muted")
                ], width=4),
                dbc.Col([
                    dbc.Progress(
                        value=min(percentage, 100),
                        color=color,
                        striped=True,
                        animated=True if percentage > 100 else False,
                        className="mb-2"
                    )
                ], width=6),
                dbc.Col([
                    html.Small(f"{percentage:.0f}%", className="text-muted")
                ], width=2)
            ], className="mb-3")
        )
    
    if not progress_bars:
        progress_bars = [html.P("No budgets created yet.", className="text-muted")]
    
    # Clear form if budget was created
    if n_clicks and category and amount:
        return progress_bars, None, "", budget_data
    
    return progress_bars, dash.no_update, dash.no_update, budget_data

@app.callback(
    Output('recent-transactions-table', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_recent_transactions(n):
    """Update recent transactions table."""
    # Mock transaction data
    transactions_data = [
        {"Date": "2025-09-24", "Description": "Grocery Store", "Category": "Food", "Amount": "₹7,097"},
        {"Date": "2025-09-23", "Description": "Petrol Station", "Category": "Transportation", "Amount": "₹3,735"},
        {"Date": "2025-09-22", "Description": "Electric Bill", "Category": "Utilities", "Amount": "₹9,960"},
        {"Date": "2025-09-21", "Description": "Restaurant", "Category": "Entertainment", "Amount": "₹5,415"},
        {"Date": "2025-09-20", "Description": "Pharmacy", "Category": "Healthcare", "Amount": "₹2,406"}
    ]
    
    table = dbc.Table.from_dataframe(
        pd.DataFrame(transactions_data),
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        className="mb-0"
    )
    
    return table


# Populate spending category dropdown with current budgets
@app.callback(
    Output('spending-category-select', 'options'),
    Input('budgets-store', 'data')
)
def update_spending_categories(budgets_data):
    """Update spending category dropdown with available budgets."""
    if not budgets_data:
        return []
    
    options = []
    for budget in budgets_data:
        options.append({
            "label": budget['name'],
            "value": budget['category']
        })
    
    return options


# Handle adding spending to budgets
@app.callback(
    [Output('spending-category-select', 'value'),
     Output('spending-amount-input', 'value'),
     Output('spending-description-input', 'value'),
     Output('budgets-store', 'data', allow_duplicate=True)],
    [Input('add-spending-btn', 'n_clicks')],
    [State('spending-category-select', 'value'),
     State('spending-amount-input', 'value'),
     State('spending-description-input', 'value'),
     State('budgets-store', 'data')],
    prevent_initial_call=True
)
def handle_add_spending(n_clicks, category, amount, description, current_budgets):
    """Handle adding spending to budgets."""
    if not n_clicks or not category or not amount:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    try:
        # Find the budget to update
        budget_data = current_budgets or []
        for budget in budget_data:
            if budget['category'] == category:
                budget['spent'] += float(amount)
                break
        
        # Clear form after successful addition
        return None, "", "", budget_data
        
    except (ValueError, TypeError):
        # Invalid input, don't update
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)