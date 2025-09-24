"""
Main Dash application for the FPTI frontend.
"""
import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
from datetime import datetime, timedelta
import json
import asyncio
import aiohttp
import os
from dotenv import load_dotenv
from yahoo_finance_service import (
    fetch_yahoo_quote, 
    fetch_yahoo_intraday, 
    search_yahoo_symbols, 
    get_market_summary
)

# Load environment variables
load_dotenv()

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
                "region": "United States",
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
                "region": "United States",
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
                "region": "United States",
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
                ], className="chart-container slide-up")
            ], width=8),
            
            # Asset Allocation Pie Chart
            dbc.Col([
                html.Div([
                    html.H4("Asset Allocation", className="chart-title"),
                    dcc.Graph(id="allocation-pie-chart", config={'displayModeBar': False})
                ], className="chart-container slide-up")
            ], width=4),
        ], className="mb-4"),
        
        dbc.Row([
            # Holdings Table
            dbc.Col([
                html.Div([
                    html.H4("Current Holdings", className="chart-title"),
                    html.Div(id="holdings-table", className="modern-table")
                ], className="chart-container slide-up")
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
                ], className="chart-container fade-in")
            ], width=6),
            
            dbc.Col([
                html.Div([
                    html.H4("Risk Analysis", className="chart-title"),
                    html.Div(id="risk-metrics")
                ], className="chart-container fade-in")
            ], width=6),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4("Sector Allocation", className="chart-title"),
                    dcc.Graph(id="sector-allocation-chart", config={'displayModeBar': False})
                ], className="chart-container slide-up")
            ], width=6),
            
            dbc.Col([
                html.Div([
                    html.H4("Asset Correlation Matrix", className="chart-title"),
                    dcc.Graph(id="correlation-matrix", config={'displayModeBar': False})
                ], className="chart-container slide-up")
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
                                    dbc.Label("Target Value ($)"),
                                    dbc.Input(
                                        id="mc-target-value",
                                        type="number",
                                        value=1000000,
                                        min=1000
                                    )
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("Time Horizon (Years)"),
                                    dbc.Input(
                                        id="mc-years",
                                        type="number",
                                        value=10,
                                        min=1,
                                        max=50
                                    )
                                ], width=6),
                            ], className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Monthly Contribution ($)"),
                                    dbc.Input(
                                        id="mc-monthly-contribution",
                                        type="number",
                                        value=1000,
                                        min=0
                                    )
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

# Navigation Click Handlers
@app.callback(
    [Output('active-tab-store', 'data'),
     Output('nav-dashboard', 'className'),
     Output('nav-analysis', 'className'),
     Output('nav-transactions', 'className'),
     Output('nav-monte-carlo', 'className'),
     Output('nav-market-data', 'className')],
    [Input('nav-dashboard', 'n_clicks'),
     Input('nav-analysis', 'n_clicks'),
     Input('nav-transactions', 'n_clicks'),
     Input('nav-monte-carlo', 'n_clicks'),
     Input('nav-market-data', 'n_clicks')],
    [State('active-tab-store', 'data')]
)
def update_navigation(dash_clicks, analysis_clicks, trans_clicks, mc_clicks, market_clicks, current_tab):
    ctx = dash.callback_context
    if not ctx.triggered:
        # Default state
        return 'dashboard', 'nav-link-custom active', 'nav-link-custom', 'nav-link-custom', 'nav-link-custom', 'nav-link-custom'
    
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
    else:
        active_tab = current_tab or 'dashboard'
    
    # Set className for each nav link
    classes = ['nav-link-custom'] * 5
    nav_mapping = {
        'dashboard': 0,
        'analysis': 1,
        'transactions': 2,
        'monte-carlo': 3,
        'market-data': 4
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
        'market-data': ('Market Data', 'Live market quotes and financial information')
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
        # Make API call to run Monte Carlo simulation
        payload = {
            "target_value": target_value or 1000000,
            "years": years or 10,
            "monthly_contribution": monthly_contribution or 1000,
            "num_simulations": num_simulations or 1000
        }
        
        response = requests.post(f"{API_BASE_URL}/analytics/portfolio/1/monte-carlo", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            
            # Create results summary
            results_summary = [
                dbc.Alert([
                    html.H5(f"Success Probability: {data['success_probability']:.1%}"),
                    html.P(f"Chance of reaching ${target_value:,} in {years} years")
                ], color="success" if data['success_probability'] > 0.5 else "warning"),
                
                html.H6("Projected Values:"),
                html.Ul([
                    html.Li(f"5th percentile: ${data['percentiles']['5th']:,.0f}"),
                    html.Li(f"25th percentile: ${data['percentiles']['25th']:,.0f}"),
                    html.Li(f"Median (50th): ${data['percentiles']['50th']:,.0f}"),
                    html.Li(f"75th percentile: ${data['percentiles']['75th']:,.0f}"),
                    html.Li(f"95th percentile: ${data['percentiles']['95th']:,.0f}"),
                ])
            ]
            
            # Create histogram chart
            # Note: In a real implementation, you'd get the full distribution data
            import numpy as np
            rng = np.random.default_rng(42)
            mock_values = rng.normal(data['percentiles']['50th'], 
                                   data['percentiles'].get('std', data['percentiles']['50th'] * 0.1), 
                                   1000)
            
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=mock_values,
                nbinsx=50,
                name='Simulation Results',
                marker={'color': '#667eea', 'opacity': 0.7},
                hovertemplate='Value Range: $%{x:,.0f}<br>Count: %{y}<extra></extra>'
            ))
            
            fig.add_vline(
                x=target_value, 
                line={'dash': "dash", 'color': "#e74c3c", 'width': 2},
                annotation={'text': f"Target: ${target_value:,}", 'font': {'color': '#e74c3c', 'size': 12}}
            )
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font={'family': 'Inter, sans-serif', 'color': '#e4e4e7'},
                xaxis_title="Portfolio Value ($)",
                yaxis_title="Frequency",
                showlegend=False
            )
            
            return results_summary, fig
        else:
            return f"Error running simulation: {response.text}", {}
            
    except Exception as e:
        return f"Error: {str(e)}", {}

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
    try:
        # Mock correlation matrix data
        import numpy as np
        
        assets = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'SPY']
        rng = np.random.default_rng(42)
        correlation_data = rng.random((5, 5))
        correlation_data = (correlation_data + correlation_data.T) / 2  # Make symmetric
        np.fill_diagonal(correlation_data, 1)  # Set diagonal to 1
        
        fig = px.imshow(
            correlation_data,
            x=assets,
            y=assets,
            color_continuous_scale=['#667eea', '#ffffff', '#e74c3c'],
            aspect="auto",
            text_auto='.2f'
        )
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_backgroundColor='rgba(0,0,0,0)',
            font={'family': 'Inter, sans-serif', 'color': '#e4e4e7'},
            xaxis={'side': 'bottom', 'showgrid': False},
            yaxis={'showgrid': False},
            margin={'l': 20, 'r': 20, 't': 20, 'b': 20}
        )
        
        fig.update_traces(
            hovertemplate='<b>%{x} vs %{y}</b><br>Correlation: %{z:.2f}<extra></extra>',
            textfont={'size': 10, 'family': 'Inter, sans-serif', 'color': '#e4e4e7'}
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creating correlation matrix: {e}")
        return {}

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

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)