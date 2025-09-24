"""
Analytics API endpoints for portfolio analysis and insights.
"""
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from ..database import get_db
from ..models import Portfolio, Holding, Transaction, Asset, PriceHistory
from ..core.utils import DataAnalyzer, MonteCarloSimulator

router = APIRouter()

class PerformanceMetrics(BaseModel):
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    var_95: float
    beta: Optional[float] = None

class MonteCarloResults(BaseModel):
    success_probability: float
    percentiles: Dict[str, float]
    scenarios: int
    target_value: float

class AllocationAnalysis(BaseModel):
    current_allocation: Dict[str, float]
    recommended_allocation: Dict[str, float]
    rebalancing_needed: bool
    rebalancing_trades: Dict[str, float]

@router.get("/portfolio/{portfolio_id}/performance", response_model=PerformanceMetrics)
async def get_portfolio_performance(
    portfolio_id: int,
    period_days: int = 365,
    benchmark_symbol: str = "^GSPC",
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Calculate portfolio performance metrics."""
    # Verify portfolio ownership
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == user_id
    ).first()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Get portfolio holdings and transactions
    holdings = db.query(Holding).filter(Holding.portfolio_id == portfolio_id).all()
    transactions = db.query(Transaction).filter(
        Transaction.portfolio_id == portfolio_id,
        Transaction.transaction_date >= datetime.now() - timedelta(days=period_days)
    ).all()
    
    if not holdings and not transactions:
        # Return zero metrics for empty portfolio
        return PerformanceMetrics(
            total_return=0.0,
            annualized_return=0.0,
            volatility=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            var_95=0.0
        )
    
    # Calculate portfolio value history (simplified)
    current_value = sum(holding.current_value for holding in holdings)
    initial_value = sum(t.total_amount for t in transactions if t.transaction_type.value == "buy")
    
    if initial_value == 0:
        total_return = 0.0
    else:
        total_return = (current_value - initial_value) / initial_value
    
    # Simplified metrics - in production, would use actual price history
    return PerformanceMetrics(
        total_return=total_return,
        annualized_return=total_return * (365 / period_days),
        volatility=0.15,  # Placeholder
        sharpe_ratio=1.2,  # Placeholder
        max_drawdown=0.08,  # Placeholder
        var_95=0.05,  # Placeholder
        beta=1.0  # Placeholder
    )

@router.post("/portfolio/{portfolio_id}/monte-carlo", response_model=MonteCarloResults)
async def run_monte_carlo_simulation(
    portfolio_id: int,
    target_value: float,
    years: int = 10,
    monthly_contribution: float = 0,
    num_simulations: int = 1000,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Run Monte Carlo simulation for portfolio projections."""
    # Verify portfolio ownership
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == user_id
    ).first()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Get current portfolio value
    holdings = db.query(Holding).filter(Holding.portfolio_id == portfolio_id).all()
    current_value = sum(holding.current_value for holding in holdings)
    
    if current_value == 0:
        raise HTTPException(status_code=400, detail="Portfolio has no value for simulation")
    
    # Use simplified assumptions for expected return and volatility
    # In production, these would be calculated from historical data
    expected_return = 0.08  # 8% annual return
    volatility = 0.15  # 15% annual volatility
    
    # Run Monte Carlo simulation
    simulated_values = MonteCarloSimulator.simulate_portfolio_returns(
        expected_return=expected_return,
        volatility=volatility,
        initial_value=current_value,
        years=years,
        num_simulations=num_simulations,
        monthly_contribution=monthly_contribution
    )
    
    # Calculate results
    success_probability = MonteCarloSimulator.calculate_retirement_probability(
        simulated_values, target_value
    )
    
    percentiles = MonteCarloSimulator.calculate_percentiles(simulated_values)
    
    return MonteCarloResults(
        success_probability=success_probability,
        percentiles=percentiles,
        scenarios=num_simulations,
        target_value=target_value
    )

@router.get("/portfolio/{portfolio_id}/allocation-analysis", response_model=AllocationAnalysis)
async def analyze_portfolio_allocation(
    portfolio_id: int,
    risk_tolerance: float = 0.5,  # 0 = conservative, 1 = aggressive
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Analyze portfolio allocation and provide rebalancing recommendations."""
    # Verify portfolio ownership
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == user_id
    ).first()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Get portfolio holdings with asset information
    holdings_query = db.query(Holding, Asset).join(Asset).filter(
        Holding.portfolio_id == portfolio_id,
        Holding.quantity > 0
    ).all()
    
    if not holdings_query:
        raise HTTPException(status_code=400, detail="Portfolio has no holdings")
    
    # Calculate current allocation
    total_value = sum(holding.current_value for holding, asset in holdings_query)
    current_allocation = {}
    
    for holding, asset in holdings_query:
        asset_type = asset.asset_type.value
        percentage = (holding.current_value / total_value) * 100
        
        if asset_type in current_allocation:
            current_allocation[asset_type] += percentage
        else:
            current_allocation[asset_type] = percentage
    
    # Generate recommended allocation based on risk tolerance
    recommended_allocation = generate_recommended_allocation(risk_tolerance)
    
    # Calculate rebalancing trades
    current_values = {
        asset_type: (percentage / 100) * total_value
        for asset_type, percentage in current_allocation.items()
    }
    
    target_values = {
        asset_type: (percentage / 100) * total_value
        for asset_type, percentage in recommended_allocation.items()
    }
    
    rebalancing_trades = DataAnalyzer.rebalance_portfolio(
        current_weights={k: v/100 for k, v in current_allocation.items()},
        target_weights={k: v/100 for k, v in recommended_allocation.items()},
        current_values=current_values,
        tolerance=0.05
    )
    
    rebalancing_needed = len(rebalancing_trades) > 0
    
    return AllocationAnalysis(
        current_allocation=current_allocation,
        recommended_allocation=recommended_allocation,
        rebalancing_needed=rebalancing_needed,
        rebalancing_trades=rebalancing_trades
    )

@router.get("/portfolio/{portfolio_id}/risk-metrics")
async def get_portfolio_risk_metrics(
    portfolio_id: int,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Get detailed risk metrics for a portfolio."""
    # Verify portfolio ownership
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == user_id
    ).first()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Get portfolio holdings
    holdings_query = db.query(Holding, Asset).join(Asset).filter(
        Holding.portfolio_id == portfolio_id,
        Holding.quantity > 0
    ).all()
    
    if not holdings_query:
        return {"message": "No holdings found for risk analysis"}
    
    # Calculate portfolio-level risk metrics
    total_value = sum(holding.current_value for holding, asset in holdings_query)
    
    # Simplified risk calculations
    return {
        "portfolio_id": portfolio_id,
        "total_value": total_value,
        "concentration_risk": calculate_concentration_risk(holdings_query, total_value),
        "sector_diversification": calculate_sector_diversification(holdings_query, total_value),
        "currency_exposure": calculate_currency_exposure(holdings_query, total_value),
        "liquidity_score": calculate_liquidity_score(holdings_query),
        "overall_risk_score": calculate_overall_risk_score(holdings_query, total_value)
    }

def generate_recommended_allocation(risk_tolerance: float) -> Dict[str, float]:
    """Generate recommended asset allocation based on risk tolerance."""
    if risk_tolerance < 0.3:
        # Conservative allocation
        return {
            "bond": 60.0,
            "stock": 30.0,
            "cash": 10.0
        }
    elif risk_tolerance < 0.7:
        # Moderate allocation
        return {
            "stock": 60.0,
            "bond": 30.0,
            "etf": 5.0,
            "cash": 5.0
        }
    else:
        # Aggressive allocation
        return {
            "stock": 80.0,
            "etf": 15.0,
            "cash": 5.0
        }

def calculate_concentration_risk(holdings_query, total_value: float) -> float:
    """Calculate concentration risk (higher = more concentrated)."""
    if total_value == 0:
        return 0.0
    
    weights = [holding.current_value / total_value for holding, asset in holdings_query]
    # Calculate Herfindahl index
    hhi = sum(w**2 for w in weights)
    return hhi

def calculate_sector_diversification(holdings_query, total_value: float) -> Dict[str, float]:
    """Calculate sector diversification."""
    sector_allocation = {}
    
    for holding, asset in holdings_query:
        sector = asset.sector or "Unknown"
        percentage = (holding.current_value / total_value) * 100
        
        if sector in sector_allocation:
            sector_allocation[sector] += percentage
        else:
            sector_allocation[sector] = percentage
    
    return sector_allocation

def calculate_currency_exposure(holdings_query, total_value: float) -> Dict[str, float]:
    """Calculate currency exposure."""
    currency_allocation = {}
    
    for holding, asset in holdings_query:
        currency = asset.currency or "USD"
        percentage = (holding.current_value / total_value) * 100
        
        if currency in currency_allocation:
            currency_allocation[currency] += percentage
        else:
            currency_allocation[currency] = percentage
    
    return currency_allocation

def calculate_liquidity_score(holdings_query) -> float:
    """Calculate overall liquidity score (0-10, higher = more liquid)."""
    # Simplified scoring based on asset type
    type_scores = {
        "stock": 9,
        "etf": 8,
        "bond": 6,
        "mutual_fund": 7,
        "cash": 10,
        "crypto": 5,
        "real_estate": 2,
        "commodity": 4
    }
    
    total_weight = 0
    weighted_score = 0
    
    for holding, asset in holdings_query:
        weight = holding.current_value
        score = type_scores.get(asset.asset_type.value, 5)
        
        weighted_score += weight * score
        total_weight += weight
    
    return weighted_score / total_weight if total_weight > 0 else 5.0

def calculate_overall_risk_score(holdings_query, total_value: float) -> float:
    """Calculate overall risk score (0-10, higher = more risky)."""
    concentration_risk = calculate_concentration_risk(holdings_query, total_value)
    liquidity_score = calculate_liquidity_score(holdings_query)
    
    # Simple risk score calculation
    # Higher concentration = higher risk
    # Lower liquidity = higher risk
    risk_score = (concentration_risk * 10) + ((10 - liquidity_score) * 0.5)
    
    return min(max(risk_score, 0), 10)  # Clamp between 0 and 10