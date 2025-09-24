"""
Main Dash application for the FPTI frontend.
"""
import dash
from dash import dcc, html, Input, Output, callback, dash_table
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
    html.Div(id='tab-content')
    
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
        return html.Div("Transactions view coming soon...")
    elif active_tab == "market-data":
        return html.Div("Market data view coming soon...")
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
    
    # Mock calculations - would use real data in production
    total_value = "$125,430.25"
    total_pnl = "+$8,430.25 (+7.21%)"
    total_holdings = "15"
    daily_change = "+$1,234.56"
    daily_change_percent = "+0.99%"
    best_performer = "AAPL"
    best_performer_change = "+2.45%"
    
    return total_value, total_pnl, total_holdings, daily_change, daily_change_percent, best_performer, best_performer_change

@app.callback(
    Output('portfolio-value-chart', 'figure'),
    Input('portfolio-data-store', 'data')
)
def update_portfolio_chart(portfolio_data):
    # Mock data for demonstration
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
    # Mock holdings data
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
            np.random.seed(42)
            mock_values = np.random.normal(data['percentiles']['50th'], 
                                         data['percentiles']['std'], 
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

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)