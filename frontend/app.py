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

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True
)

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

# App Layout
app.layout = dbc.Container([
    dcc.Store(id='portfolio-data-store'),
    dcc.Store(id='market-data-store'),
    dcc.Interval(
        id='interval-component',
        interval=5*60*1000,  # Update every 5 minutes
        n_intervals=0
    ),
    
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("Financial Portfolio Dashboard", 
                   className="text-center mb-4"),
            html.Hr()
        ])
    ]),
    
    # Navigation Tabs
    dbc.Row([
        dbc.Col([
            dbc.Tabs([
                dbc.Tab(label="Dashboard", tab_id="dashboard"),
                dbc.Tab(label="Portfolio Analysis", tab_id="analysis"),
                dbc.Tab(label="Transactions", tab_id="transactions"),
                dbc.Tab(label="Monte Carlo", tab_id="monte-carlo"),
                dbc.Tab(label="Market Data", tab_id="market-data"),
            ], id="tabs", active_tab="dashboard")
        ])
    ], className="mb-4"),
    
    # Tab Content
    html.Div(id='tab-content'),
    
    # Error notifications
    html.Div(id='error-notifications', className="position-fixed", style={'top': '20px', 'right': '20px', 'zIndex': 9999})
    
], fluid=True)

# Dashboard Tab Content
def create_dashboard_layout():
    return [
        dbc.Row([
            # Portfolio Summary Cards
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Total Portfolio Value", className="card-title"),
                        html.H2(id="total-value", className="text-success"),
                        html.P(id="total-pnl", className="card-text")
                    ])
                ])
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Number of Holdings", className="card-title"),
                        html.H2(id="total-holdings", className="text-info"),
                        html.P("Active Positions", className="card-text")
                    ])
                ])
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Today's Change", className="card-title"),
                        html.H2(id="daily-change", className="text-warning"),
                        html.P(id="daily-change-percent", className="card-text")
                    ])
                ])
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Best Performer", className="card-title"),
                        html.H2(id="best-performer", className="text-success"),
                        html.P(id="best-performer-change", className="card-text")
                    ])
                ])
            ], width=3),
        ], className="mb-4"),
        
        dbc.Row([
            # Portfolio Value Chart
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Portfolio Value Over Time"),
                        dcc.Graph(id="portfolio-value-chart")
                    ])
                ])
            ], width=8),
            
            # Asset Allocation Pie Chart
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Asset Allocation"),
                        dcc.Graph(id="allocation-pie-chart")
                    ])
                ])
            ], width=4),
        ], className="mb-4"),
        
        dbc.Row([
            # Holdings Table
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Current Holdings"),
                        html.Div(id="holdings-table")
                    ])
                ])
            ])
        ])
    ]

# Portfolio Analysis Tab Content
def create_analysis_layout():
    return [
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Performance Metrics"),
                        html.Div(id="performance-metrics")
                    ])
                ])
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Risk Analysis"),
                        html.Div(id="risk-metrics")
                    ])
                ])
            ], width=6),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Sector Allocation"),
                        dcc.Graph(id="sector-allocation-chart")
                    ])
                ])
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Asset Correlation Matrix"),
                        dcc.Graph(id="correlation-matrix")
                    ])
                ])
            ], width=6),
        ])
    ]

# Transactions Tab Content
def create_transactions_layout():
    return [
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Add New Transaction"),
                        dbc.Form([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Portfolio"),
                                    dcc.Dropdown(
                                        id="trans-portfolio-dropdown",
                                        placeholder="Select Portfolio"
                                    )
                                ], width=6),
                                dbc.Col([
                                    dbc.Label("Asset Symbol"),
                                    dbc.Input(
                                        id="trans-symbol-input",
                                        type="text",
                                        placeholder="e.g., AAPL"
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
                                        placeholder="Select Type"
                                    )
                                ], width=4),
                                dbc.Col([
                                    dbc.Label("Quantity"),
                                    dbc.Input(
                                        id="trans-quantity-input",
                                        type="number",
                                        min=0,
                                        step=0.01
                                    )
                                ], width=4),
                                dbc.Col([
                                    dbc.Label("Price per Share"),
                                    dbc.Input(
                                        id="trans-price-input",
                                        type="number",
                                        min=0,
                                        step=0.01
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
                                        color="primary",
                                        className="mt-2"
                                    )
                                ], width=6),
                            ], className="mb-3"),
                        ])
                    ])
                ])
            ])
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Transaction History"),
                        dbc.Row([
                            dbc.Col([
                                dcc.Dropdown(
                                    id="trans-filter-portfolio",
                                    placeholder="Filter by Portfolio",
                                    className="mb-3"
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
                                    className="mb-3"
                                )
                            ], width=4),
                            dbc.Col([
                                dbc.Button(
                                    "Refresh",
                                    id="refresh-transactions-btn",
                                    color="secondary",
                                    className="mb-3"
                                )
                            ], width=4),
                        ]),
                        html.Div(id="transactions-table"),
                        html.Div(id="transaction-add-result", className="mt-3")
                    ])
                ])
            ])
        ])
    ]

# Market Data Tab Content
def create_market_data_layout():
    return [
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Market Summary"),
                        html.Div(id="market-summary")
                    ])
                ])
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Stock Quote Lookup"),
                        dbc.InputGroup([
                            dbc.Input(
                                id="stock-symbol-input",
                                placeholder="Enter symbol (e.g., AAPL)"
                            ),
                            dbc.Button(
                                "Get Quote",
                                id="get-quote-btn",
                                color="info"
                            )
                        ], className="mb-3"),
                        html.Div(id="stock-quote-result")
                    ])
                ])
            ], width=6),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Watchlist"),
                        html.Div(id="watchlist-table")
                    ])
                ])
            ], width=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Market Movers"),
                        html.Div(id="market-movers")
                    ])
                ])
            ], width=4),
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

# Tab Content Callback
@app.callback(
    Output('tab-content', 'children'),
    Input('tabs', 'active_tab')
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
    return html.Div("Select a tab")

# Data Loading Callbacks
@app.callback(
    [Output('portfolio-data-store', 'data'),
     Output('market-data-store', 'data')],
    Input('interval-component', 'n_intervals')
)
def load_data(n):
    try:
        # Load portfolio data
        portfolio_response = requests.get(f"{API_BASE_URL}/portfolios/")
        portfolios = portfolio_response.json() if portfolio_response.status_code == 200 else []
        
        # Load market summary
        market_response = requests.get(f"{API_BASE_URL}/market-data/summary")
        market_data = market_response.json() if market_response.status_code == 200 else {}
        
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
            line=dict(color='#28a745', width=2)
        ))
        
        fig.update_layout(
            title="Portfolio Value Trend",
            xaxis_title="Date",
            yaxis_title="Value ($)",
            hovermode='x unified',
            showlegend=False
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
        title="Asset Allocation"
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
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
            {'name': 'Avg Cost', 'id': 'Avg Cost', 'type': 'numeric', 'format': '$,.2f'},
            {'name': 'Current Price', 'id': 'Current Price', 'type': 'numeric', 'format': '$,.2f'},
            {'name': 'Market Value', 'id': 'Market Value', 'type': 'numeric', 'format': '$,.0f'},
            {'name': 'P&L', 'id': 'P&L', 'type': 'numeric', 'format': '$,.0f'},
            {'name': 'P&L %', 'id': 'P&L %', 'type': 'numeric', 'format': '.2f%'},
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
                name='Simulation Results'
            ))
            
            fig.add_vline(x=target_value, line_dash="dash", line_color="red",
                         annotation_text=f"Target: ${target_value:,}")
            
            fig.update_layout(
                title="Monte Carlo Simulation Results",
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
                {"name": "Price", "id": "Price", "type": "numeric", "format": "$,.2f"},
                {"name": "Total", "id": "Total", "type": "numeric", "format": "$,.2f"},
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

# Market Data Callbacks
@app.callback(
    Output('market-summary', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_market_summary(n):
    try:
        response = requests.get(f"{API_BASE_URL}/market-data/summary")
        if response.status_code == 200:
            data = response.json()
            return [
                html.H6("Market Status: Open", className="text-success"),
                html.P(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            ]
        else:
            return html.P("Market data unavailable")
    except Exception as e:
        return html.P(f"Error loading market data: {str(e)}")

@app.callback(
    Output('stock-quote-result', 'children'),
    [Input('get-quote-btn', 'n_clicks')],
    [State('stock-symbol-input', 'value')]
)
def get_stock_quote(n_clicks, symbol):
    if not n_clicks or not symbol:
        return ""
    
    try:
        response = requests.get(f"{API_BASE_URL}/market-data/{symbol.upper()}")
        if response.status_code == 200:
            data = response.json()
            return dbc.Card([
                dbc.CardBody([
                    html.H5(f"{symbol.upper()}", className="card-title"),
                    html.H4(f"${data.get('current_price', 'N/A')}", className="text-primary"),
                    html.P(f"Change: {data.get('change', 'N/A')} ({data.get('change_percent', 'N/A')}%)")
                ])
            ])
        else:
            return dbc.Alert(f"Quote not found for {symbol}", color="warning")
    except Exception as e:
        return dbc.Alert(f"Error: {str(e)}", color="danger")

@app.callback(
    Output('watchlist-table', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_watchlist(n):
    # Mock watchlist for now
    watchlist_data = {
        'Symbol': ['AAPL', 'GOOGL', 'MSFT', 'TSLA'],
        'Price': [175.50, 2850.00, 340.25, 245.80],
        'Change': ['+2.50', '+15.30', '-1.25', '+8.90'],
        'Change %': ['+1.45%', '+0.54%', '-0.37%', '+3.75%']
    }
    
    df = pd.DataFrame(watchlist_data)
    
    return dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[
            {"name": "Symbol", "id": "Symbol"},
            {"name": "Price", "id": "Price", "type": "numeric", "format": "$,.2f"},
            {"name": "Change", "id": "Change"},
            {"name": "Change %", "id": "Change %"},
        ],
        style_cell={'textAlign': 'center'}
    )

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
            title="Sector Allocation",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(showlegend=True)
        
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
            color_continuous_scale='RdBu',
            aspect="auto",
            title="Asset Correlation Matrix"
        )
        
        fig.update_layout(
            xaxis={'side': 'bottom'},
            width=400,
            height=400
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

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)