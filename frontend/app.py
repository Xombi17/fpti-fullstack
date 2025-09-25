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
CURRENCY_FORMAT = '$,.0f'

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
        quote_data = fetch_yahoo_quote(symbol)
        if quote_data:
            return quote_data
        else:
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
            "change_percent": "-0.64"
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
            "change_percent": "-0.17"
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
            "change_percent": "0.26"
        }
    }
    
    # Return specific mock data if available, otherwise generic
    if symbol in mock_data:
        return mock_data[symbol]
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
            "change_percent": "0.63"
        }

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
                                        ]
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
                                        ]
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
                                className="mb-3"
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
                                        placeholder="Choose category..."
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
        # Mock portfolio data for demo
        portfolios = [{
            'id': 1,
            'name': 'My Portfolio',
            'holdings': [
                {'asset': {'symbol': 'AAPL'}, 'quantity': 10},
                {'asset': {'symbol': 'GOOGL'}, 'quantity': 5},
                {'asset': {'symbol': 'MSFT'}, 'quantity': 8}
            ]
        }]
        
        # Load market summary
        market_summary = fetch_market_summary()
        
        # Get portfolio symbols for live prices
        symbols = ['AAPL', 'GOOGL', 'MSFT']  # Demo symbols
        
        # Fetch live prices for portfolio symbols (mock data for demo)
        live_quotes = {
            'AAPL': {
                'symbol': 'AAPL',
                'price': 176.80,
                'change': 1.50,
                'change_percent': '0.86',
                'volume': 45000000,
                'timestamp': datetime.now().isoformat()
            },
            'GOOGL': {
                'symbol': 'GOOGL',
                'price': 2850.25,
                'change': -15.30,
                'change_percent': '-0.53',
                'volume': 1250000,
                'timestamp': datetime.now().isoformat()
            },
            'MSFT': {
                'symbol': 'MSFT',
                'price': 428.90,
                'change': 3.25,
                'change_percent': '0.76',
                'volume': 18500000,
                'timestamp': datetime.now().isoformat()
            }
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
        return "$0.00", "No P&L data", "0", "$0.00", "0.00%", "N/A", "N/A"
    
    try:
        # Calculate real values from portfolio data
        total_value = 0
        total_holdings = 0
        
        for portfolio in portfolio_data:
            # Get portfolio value from API
            try:
                value_response = requests.get(f"{API_BASE_URL}/portfolios/{portfolio['id']}/value")
                if value_response.status_code == 200:
                    portfolio_value = value_response.json()
                    total_value += portfolio_value.get('current_value', 0)
            except Exception as e:
                print(f"Error getting portfolio value: {e}")
            
            # Count holdings
            try:
                holdings_response = requests.get(f"{API_BASE_URL}/portfolios/{portfolio['id']}/holdings")
                if holdings_response.status_code == 200:
                    holdings = holdings_response.json()
                    total_holdings += len(holdings)
            except Exception as e:
                print(f"Error getting holdings: {e}")
        
        # Format values
        total_value_str = f"${total_value:,.2f}"
        total_pnl = f"${total_value * 0.071:,.2f} (+7.1%)"  # Mock P&L calculation
        total_holdings_str = str(total_holdings)
        daily_change = f"${total_value * 0.0099:,.2f}"
        daily_change_percent = "+0.99%"
        best_performer = "AAPL"  # Would need market data to calculate
        best_performer_change = "+2.45%"
        
        return total_value_str, total_pnl, total_holdings_str, daily_change, daily_change_percent, best_performer, best_performer_change
        
    except Exception as e:
        print(f"Error updating dashboard cards: {e}")
        # Fallback to mock data
        return "$125,430.25", "+$8,430.25 (+7.21%)", "15", "+$1,234.56", "+0.99%", "AAPL", "+2.45%"

@app.callback(
    Output('portfolio-value-chart', 'figure'),
    Input('portfolio-data-store', 'data')
)
def update_portfolio_chart(portfolio_data):
    try:
        if not portfolio_data:
            # Fallback to mock data
            dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
            values = [100000 + i*10 + (i%30)*500 for i in range(len(dates))]
        else:
            # Try to get historical data from API
            try:
                # Get the first portfolio for demo
                portfolio_id = portfolio_data[0]['id']
                response = requests.get(f"{API_BASE_URL}/analytics/portfolio/{portfolio_id}/performance")
                
                if response.status_code == 200:
                    perf_data = response.json()
                    if 'historical_values' in perf_data:
                        hist_data = perf_data['historical_values']
                        dates = pd.to_datetime([item['date'] for item in hist_data])
                        values = [item['value'] for item in hist_data]
                    else:
                        # Fallback to mock data
                        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
                        values = [100000 + i*10 + (i%30)*500 for i in range(len(dates))]
                else:
                    # Fallback to mock data
                    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
                    values = [100000 + i*10 + (i%30)*500 for i in range(len(dates))]
            except Exception as e:
                print(f"Error getting historical data: {e}")
                # Fallback to mock data
                dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
                values = [100000 + i*10 + (i%30)*500 for i in range(len(dates))]
        
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
                'title': {'text': 'Portfolio Value ($)', 'font': {'size': 14, 'color': '#a1a1aa'}},
                'showgrid': True,
                'gridcolor': 'rgba(161, 161, 170, 0.2)',
                'showline': False,
                'zeroline': False,
                'tickformat': '$,.0f',
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
    # Mock allocation data
    allocation_data = {
        'Asset Type': ['Stocks', 'Bonds', 'ETFs', 'Cash'],
        'Percentage': [65, 20, 10, 5],
        'Value': [81530, 25086, 12543, 6271]
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
        hovertemplate='<b>%{label}</b><br>Value: $%{value:,.0f}<br>Percentage: %{percent}<extra></extra>',
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
    Input('portfolio-data-store', 'data')
)
def update_holdings_table(portfolio_data):
    if not portfolio_data:
        # Fallback to mock data if no portfolio data
        holdings_data = {
            'Symbol': ['No Data'],
            'Shares': [0],
            'Avg Cost': [0.00],
            'Current Price': [0.00],
            'Market Value': [0],
            'P&L': [0],
            'P&L %': [0.0]
        }
        df = pd.DataFrame(holdings_data)
    else:
        try:
            # Get real holdings data from API
            all_holdings = []
            
            for portfolio in portfolio_data:
                try:
                    holdings_response = requests.get(f"{API_BASE_URL}/portfolios/{portfolio['id']}/holdings")
                    if holdings_response.status_code == 200:
                        holdings = holdings_response.json()
                        for holding in holdings:
                            # Get current price for the asset
                            try:
                                price_response = requests.get(f"{API_BASE_URL}/market-data/{holding['asset']['symbol']}")
                                current_price = price_response.json().get('current_price', 0) if price_response.status_code == 200 else 0
                            except:
                                current_price = 0
                            
                            # Calculate values
                            market_value = holding['quantity'] * current_price
                            cost_basis = holding['quantity'] * holding['average_cost']
                            pnl = market_value - cost_basis
                            pnl_percent = (pnl / cost_basis * 100) if cost_basis > 0 else 0
                            
                            all_holdings.append({
                                'Symbol': holding['asset']['symbol'],
                                'Shares': holding['quantity'],
                                'Avg Cost': holding['average_cost'],
                                'Current Price': current_price,
                                'Market Value': market_value,
                                'P&L': pnl,
                                'P&L %': pnl_percent
                            })
                except Exception as e:
                    print(f"Error getting holdings for portfolio {portfolio['id']}: {e}")
            
            if all_holdings:
                df = pd.DataFrame(all_holdings)
            else:
                # Fallback to mock data
                holdings_data = {
                    'Symbol': ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'],
                    'Shares': [100, 50, 75, 25, 30],
                    'Avg Cost': [150.00, 2800.00, 300.00, 800.00, 3200.00],
                    'Current Price': [175.00, 2950.00, 350.00, 750.00, 3400.00],
                    'Market Value': [17500, 147500, 26250, 18750, 102000],
                    'P&L': [2500, 7500, 3750, -1250, 6000],
                    'P&L %': [16.67, 5.36, 16.67, -6.25, 6.25]
                }
                df = pd.DataFrame(holdings_data)
                
        except Exception as e:
            print(f"Error processing holdings data: {e}")
            # Fallback to mock data
            holdings_data = {
                'Symbol': ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'],
                'Shares': [100, 50, 75, 25, 30],
                'Avg Cost': [150.00, 2800.00, 300.00, 800.00, 3200.00],
                'Current Price': [175.00, 2950.00, 350.00, 750.00, 3400.00],
                'Market Value': [17500, 147500, 26250, 18750, 102000],
                'P&L': [2500, 7500, 3750, -1250, 6000],
                'P&L %': [16.67, 5.36, 16.67, -6.25, 6.25]
            }
            df = pd.DataFrame(holdings_data)
    
    return dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[
            {'name': 'Symbol', 'id': 'Symbol'},
            {'name': 'Shares', 'id': 'Shares', 'type': 'numeric'},
            {'name': 'Avg Cost', 'id': 'Avg Cost', 'type': 'numeric', 'format': {'specifier': '$,.2f'}},
            {'name': 'Current Price', 'id': 'Current Price', 'type': 'numeric', 'format': {'specifier': '$,.2f'}},
            {'name': 'Market Value', 'id': 'Market Value', 'type': 'numeric', 'format': {'specifier': '$,.0f'}},
            {'name': 'P&L', 'id': 'P&L', 'type': 'numeric', 'format': {'specifier': '$,.0f'}},
            {'name': 'P&L %', 'id': 'P&L %', 'type': 'numeric', 'format': {'specifier': '.2%'}},
        ],
        style_cell={'textAlign': 'center'},
        style_data_conditional=[
            {
                'if': {'filter_query': '{P&L} > 0'},
                'backgroundColor': '#d4edda',
                'color': 'black',
            },
            {
                'if': {'filter_query': '{P&L} < 0'},
                'backgroundColor': '#f8d7da',
                'color': 'black',
            }
        ]
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
        response = requests.get(f"{API_BASE_URL}/portfolios/")
        if response.status_code == 200:
            portfolios = response.json()
            options = [{"label": p["name"], "value": p["id"]} for p in portfolios]
            return options, [{"label": "All", "value": "ALL"}] + options
        return [], [{"label": "All", "value": "ALL"}]
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
        # First, ensure asset exists
        asset_data = {"symbol": symbol, "name": symbol, "asset_type": "STOCK"}
        requests.post(f"{API_BASE_URL}/assets/", json=asset_data)
        
        # Add transaction
        transaction_data = {
            "portfolio_id": portfolio_id,
            "asset_symbol": symbol,
            "transaction_type": trans_type,
            "quantity": float(quantity),
            "price": float(price),
            "transaction_date": date
        }
        
        response = requests.post(f"{API_BASE_URL}/transactions/", json=transaction_data)
        if response.status_code == 200:
            return dbc.Alert("Transaction added successfully!", color="success", dismissable=True)
        else:
            return dbc.Alert(f"Error adding transaction: {response.text}", color="danger", dismissable=True)
    
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
        response = requests.get(f"{API_BASE_URL}/transactions/")
        if response.status_code != 200:
            return html.P("No transactions found")
        
        transactions = response.json()
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
                {"name": "Price", "id": "Price", "type": "numeric", "format": {"specifier": "$,.2f"}},
                {"name": "Total", "id": "Total", "type": "numeric", "format": {"specifier": "$,.2f"}},
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

# Portfolio Analysis Callbacks
@app.callback(
    Output('performance-metrics', 'children'),
    Input('portfolio-data-store', 'data')
)
def update_performance_metrics(portfolio_data):
    try:
        if not portfolio_data:
            return html.P("No portfolio data available")
        
        # Mock performance calculations - would use real analytics API
        metrics = [
            {"metric": "Total Return", "value": "12.5%", "color": "success"},
            {"metric": "Annualized Return", "value": "8.7%", "color": "success"},
            {"metric": "Volatility", "value": "16.2%", "color": "warning"},
            {"metric": "Sharpe Ratio", "value": "1.23", "color": "info"},
            {"metric": "Max Drawdown", "value": "-8.5%", "color": "danger"},
            {"metric": "Beta", "value": "0.95", "color": "secondary"}
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
        
        # Mock risk calculations
        risk_metrics = [
            {"metric": "Value at Risk (95%)", "value": "$12,450", "color": "danger"},
            {"metric": "Expected Shortfall", "value": "$18,230", "color": "danger"},
            {"metric": "Concentration Risk", "value": "Medium", "color": "warning"},
            {"metric": "Liquidity Score", "value": "High", "color": "success"},
            {"metric": "Correlation to S&P 500", "value": "0.87", "color": "info"},
            {"metric": "Tracking Error", "value": "4.2%", "color": "secondary"}
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
        # Mock sector allocation data
        sectors = ['Technology', 'Healthcare', 'Financial Services', 'Consumer Goods', 'Energy']
        values = [35, 20, 15, 20, 10]
        
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
        # Use a fixed set of reliable assets
        assets = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        print(f"DEBUG: Creating correlation matrix for: {assets}")
        
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
                                html.H5(f"${price:,.2f}", className="text-info mb-0"),
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
    
    quote_data = fetch_detailed_quote(symbol.upper())
    if not quote_data:
        return dbc.Alert("Quote not found or API error", color="danger")
    
    change_color = "success" if quote_data['change'] >= 0 else "danger"
    change_icon = "fa-arrow-up" if quote_data['change'] >= 0 else "fa-arrow-down"
    
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H4(quote_data['symbol'], className="mb-1"),
                    html.H3(f"${quote_data['price']:.2f}", className="text-primary mb-0")
                ], width=6),
                dbc.Col([
                    html.P([
                        html.I(className=f"fas {change_icon} me-1"),
                        f"${quote_data['change']:.2f} ({quote_data['change_percent']}%)"
                    ], className=f"text-{change_color} mb-1"),
                    html.Small(f"Volume: {quote_data['volume']:,}", className="text-muted")
                ], width=6, className="text-end")
            ]),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.Small("Open", className="text-muted d-block"),
                    html.Strong(f"${quote_data['open']:.2f}")
                ], width=3),
                dbc.Col([
                    html.Small("High", className="text-muted d-block"),
                    html.Strong(f"${quote_data['high']:.2f}")
                ], width=3),
                dbc.Col([
                    html.Small("Low", className="text-muted d-block"),
                    html.Strong(f"${quote_data['low']:.2f}")
                ], width=3),
                dbc.Col([
                    html.Small("Prev Close", className="text-muted d-block"),
                    html.Strong(f"${quote_data['previous_close']:.2f}")
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
                "Price": f"${quote['price']:.2f}",
                "Change": f"${quote['change']:.2f}",
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
        return {}, ""
    
    intraday_data = fetch_intraday_data(symbol.upper(), interval)
    if not intraday_data or 'data' not in intraday_data:
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
    
    fig.update_layout(
        title=f"{symbol.upper()} - {interval} Intraday Chart",
        xaxis_title="Time",
        yaxis_title="Price ($)",
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