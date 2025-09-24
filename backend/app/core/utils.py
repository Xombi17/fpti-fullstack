"""
Utility functions for the FPTI application.
"""
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import asyncio
import aiohttp
from ..core.config import settings


class DataAnalyzer:
    """Utility class for financial data analysis using Pandas."""
    
    @staticmethod
    def calculate_returns(prices: pd.Series, method: str = "simple") -> pd.Series:
        """
        Calculate returns from price series.
        
        Args:
            prices: Price series
            method: 'simple' or 'log'
            
        Returns:
            Returns series
        """
        if method == "log":
            return np.log(prices / prices.shift(1))
        else:
            return prices.pct_change()
    
    @staticmethod
    def calculate_volatility(returns: pd.Series, periods: int = 252) -> float:
        """
        Calculate annualized volatility.
        
        Args:
            returns: Returns series
            periods: Number of periods in a year (252 for daily, 12 for monthly)
            
        Returns:
            Annualized volatility
        """
        return returns.std() * np.sqrt(periods)
    
    @staticmethod
    def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02, 
                             periods: int = 252) -> float:
        """
        Calculate Sharpe ratio.
        
        Args:
            returns: Returns series
            risk_free_rate: Risk-free rate (annual)
            periods: Number of periods in a year
            
        Returns:
            Sharpe ratio
        """
        excess_returns = returns - (risk_free_rate / periods)
        return excess_returns.mean() / returns.std() * np.sqrt(periods)
    
    @staticmethod
    def calculate_max_drawdown(prices: pd.Series) -> float:
        """
        Calculate maximum drawdown.
        
        Args:
            prices: Price series
            
        Returns:
            Maximum drawdown as a percentage
        """
        cumulative = (1 + DataAnalyzer.calculate_returns(prices)).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    @staticmethod
    def calculate_var(returns: pd.Series, confidence_level: float = 0.05) -> float:
        """
        Calculate Value at Risk (VaR).
        
        Args:
            returns: Returns series
            confidence_level: Confidence level (0.05 for 95% VaR)
            
        Returns:
            VaR value
        """
        return returns.quantile(confidence_level)
    
    @staticmethod
    def calculate_beta(asset_returns: pd.Series, market_returns: pd.Series) -> float:
        """
        Calculate beta relative to market.
        
        Args:
            asset_returns: Asset returns series
            market_returns: Market returns series
            
        Returns:
            Beta value
        """
        covariance = asset_returns.cov(market_returns)
        market_variance = market_returns.var()
        return covariance / market_variance if market_variance != 0 else 0
    
    @staticmethod
    def calculate_correlation_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate correlation matrix for multiple assets.
        
        Args:
            returns_df: DataFrame with returns for multiple assets
            
        Returns:
            Correlation matrix
        """
        return returns_df.corr()
    
    @staticmethod
    def rebalance_portfolio(current_weights: Dict[str, float], 
                          target_weights: Dict[str, float],
                          current_values: Dict[str, float],
                          tolerance: float = 0.05) -> Dict[str, float]:
        """
        Calculate rebalancing trades needed.
        
        Args:
            current_weights: Current portfolio weights
            target_weights: Target portfolio weights
            current_values: Current values of each position
            tolerance: Rebalancing tolerance
            
        Returns:
            Dictionary of trades needed (positive = buy, negative = sell)
        """
        total_value = sum(current_values.values())
        trades = {}
        
        for asset in target_weights:
            current_weight = current_weights.get(asset, 0)
            target_weight = target_weights[asset]
            weight_diff = target_weight - current_weight
            
            if abs(weight_diff) > tolerance:
                trade_value = weight_diff * total_value
                trades[asset] = trade_value
        
        return trades


class MonteCarloSimulator:
    """Monte Carlo simulation for financial projections."""
    
    @staticmethod
    def simulate_portfolio_returns(expected_return: float, volatility: float,
                                 initial_value: float, years: int,
                                 num_simulations: int = 1000,
                                 monthly_contribution: float = 0) -> np.ndarray:
        """
        Simulate portfolio value over time using Monte Carlo.
        
        Args:
            expected_return: Expected annual return
            volatility: Annual volatility
            initial_value: Initial portfolio value
            years: Number of years to simulate
            num_simulations: Number of simulation paths
            monthly_contribution: Monthly contribution amount
            
        Returns:
            Array of final portfolio values
        """
        # Convert to monthly parameters
        monthly_return = expected_return / 12
        monthly_volatility = volatility / np.sqrt(12)
        months = years * 12
        
        # Generate random returns
        np.random.seed(42)  # For reproducibility
        random_returns = np.random.normal(
            monthly_return, monthly_volatility, (num_simulations, months)
        )
        
        # Simulate portfolio values
        final_values = np.zeros(num_simulations)
        
        for i in range(num_simulations):
            value = initial_value
            for month in range(months):
                # Apply return
                value *= (1 + random_returns[i, month])
                # Add monthly contribution
                value += monthly_contribution
            
            final_values[i] = value
        
        return final_values
    
    @staticmethod
    def calculate_retirement_probability(simulated_values: np.ndarray,
                                       target_value: float) -> float:
        """
        Calculate probability of reaching retirement target.
        
        Args:
            simulated_values: Array of simulated final values
            target_value: Target retirement value
            
        Returns:
            Probability of success (0-1)
        """
        successful_simulations = np.sum(simulated_values >= target_value)
        return successful_simulations / len(simulated_values)
    
    @staticmethod
    def calculate_percentiles(simulated_values: np.ndarray) -> Dict[str, float]:
        """
        Calculate key percentiles of simulated values.
        
        Args:
            simulated_values: Array of simulated values
            
        Returns:
            Dictionary of percentiles
        """
        return {
            "5th": np.percentile(simulated_values, 5),
            "25th": np.percentile(simulated_values, 25),
            "50th": np.percentile(simulated_values, 50),
            "75th": np.percentile(simulated_values, 75),
            "95th": np.percentile(simulated_values, 95),
            "mean": np.mean(simulated_values),
            "std": np.std(simulated_values)
        }


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format amount as currency string."""
    if currency == "USD":
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def calculate_compound_interest(principal: float, rate: float, years: int,
                              compounds_per_year: int = 12) -> float:
    """Calculate compound interest."""
    return principal * (1 + rate / compounds_per_year) ** (compounds_per_year * years)


def calculate_required_savings(target_amount: float, years: int, 
                             annual_return: float, 
                             monthly_contribution: bool = True) -> float:
    """
    Calculate required monthly/annual savings to reach target.
    
    Args:
        target_amount: Target amount to reach
        years: Number of years
        annual_return: Expected annual return
        monthly_contribution: If True, return monthly amount; if False, annual
        
    Returns:
        Required savings amount
    """
    if monthly_contribution:
        periods = years * 12
        rate = annual_return / 12
    else:
        periods = years
        rate = annual_return
    
    # Future value of annuity formula
    if rate == 0:
        return target_amount / periods
    
    return target_amount * rate / ((1 + rate) ** periods - 1)