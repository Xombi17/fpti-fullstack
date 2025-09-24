"""
Core financial classes implementing OOP principles for the FPTI application.
These classes encapsulate business logic and financial calculations.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd
import numpy as np
from enum import Enum


class AssetClass(Enum):
    """Asset classification for portfolio analysis."""
    EQUITY = "equity"
    FIXED_INCOME = "fixed_income"
    COMMODITY = "commodity"
    REAL_ESTATE = "real_estate"
    CASH = "cash"
    ALTERNATIVE = "alternative"


class RiskLevel(Enum):
    """Risk level classification."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    VERY_AGGRESSIVE = "very_aggressive"


@dataclass
class MarketData:
    """Data class for market information."""
    symbol: str
    price: float
    timestamp: datetime
    volume: Optional[int] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None


@dataclass
class PerformanceMetrics:
    """Data class for portfolio performance metrics."""
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    var_95: float  # Value at Risk 95%
    beta: Optional[float] = None


class FinancialInstrument(ABC):
    """Abstract base class for all financial instruments."""
    
    def __init__(self, symbol: str, name: str, asset_class: AssetClass):
        self.symbol = symbol
        self.name = name
        self.asset_class = asset_class
        self._current_price: Optional[float] = None
        self._last_updated: Optional[datetime] = None
    
    @property
    def current_price(self) -> Optional[float]:
        """Get current market price."""
        return self._current_price
    
    @current_price.setter
    def current_price(self, price: float):
        """Set current market price with timestamp."""
        self._current_price = price
        self._last_updated = datetime.now()
    
    @abstractmethod
    def calculate_value(self, quantity: float) -> float:
        """Calculate total value for given quantity."""
        pass
    
    @abstractmethod
    def get_risk_metrics(self) -> Dict[str, float]:
        """Get risk metrics for this instrument."""
        pass


class Stock(FinancialInstrument):
    """Stock implementation of financial instrument."""
    
    def __init__(self, symbol: str, name: str, sector: str = "", industry: str = ""):
        super().__init__(symbol, name, AssetClass.EQUITY)
        self.sector = sector
        self.industry = industry
        self.dividend_yield: float = 0.0
        self.pe_ratio: Optional[float] = None
        self.market_cap: Optional[float] = None
    
    def calculate_value(self, quantity: float) -> float:
        """Calculate total value of stock position."""
        if self._current_price is None:
            raise ValueError(f"No current price available for {self.symbol}")
        return quantity * self._current_price
    
    def get_risk_metrics(self) -> Dict[str, float]:
        """Get risk metrics for stock."""
        # This would typically be calculated from historical data
        return {
            "beta": 1.0,  # Placeholder
            "volatility": 0.25,  # Placeholder
            "correlation_to_market": 0.8  # Placeholder
        }


class Bond(FinancialInstrument):
    """Bond implementation of financial instrument."""
    
    def __init__(self, symbol: str, name: str, coupon_rate: float, 
                 maturity_date: datetime, face_value: float = 1000):
        super().__init__(symbol, name, AssetClass.FIXED_INCOME)
        self.coupon_rate = coupon_rate
        self.maturity_date = maturity_date
        self.face_value = face_value
        self.credit_rating: Optional[str] = None
        self.duration: Optional[float] = None
    
    def calculate_value(self, quantity: float) -> float:
        """Calculate total value of bond position."""
        if self._current_price is None:
            # Use face value if no market price available
            return quantity * self.face_value
        return quantity * self._current_price
    
    def get_risk_metrics(self) -> Dict[str, float]:
        """Get risk metrics for bond."""
        return {
            "duration": self.duration or 5.0,  # Placeholder
            "credit_risk": 0.02,  # Placeholder
            "interest_rate_sensitivity": 0.05  # Placeholder
        }


class Position:
    """Represents a position in a financial instrument."""
    
    def __init__(self, instrument: FinancialInstrument, quantity: float, 
                 average_cost: float, purchase_date: datetime):
        self.instrument = instrument
        self.quantity = quantity
        self.average_cost = average_cost
        self.purchase_date = purchase_date
    
    @property
    def current_value(self) -> float:
        """Calculate current market value of position."""
        return self.instrument.calculate_value(self.quantity)
    
    @property
    def cost_basis(self) -> float:
        """Calculate total cost basis of position."""
        return self.quantity * self.average_cost
    
    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized profit/loss."""
        return self.current_value - self.cost_basis
    
    @property
    def unrealized_pnl_percent(self) -> float:
        """Calculate unrealized profit/loss percentage."""
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100
    
    def add_shares(self, quantity: float, price: float) -> None:
        """Add shares to position and update average cost."""
        total_cost = self.cost_basis + (quantity * price)
        self.quantity += quantity
        self.average_cost = total_cost / self.quantity if self.quantity > 0 else 0
    
    def remove_shares(self, quantity: float) -> float:
        """Remove shares from position and return realized P&L."""
        if quantity > self.quantity:
            raise ValueError("Cannot remove more shares than owned")
        
        current_price = self.instrument.current_price
        if current_price is None:
            raise ValueError("Cannot determine current price for sale")
        
        realized_pnl = quantity * (current_price - self.average_cost)
        self.quantity -= quantity
        return realized_pnl


class Portfolio:
    """Portfolio class managing a collection of positions."""
    
    def __init__(self, name: str, owner: str, initial_cash: float = 0.0):
        self.name = name
        self.owner = owner
        self.positions: Dict[str, Position] = {}
        self.cash = initial_cash
        self.inception_date = datetime.now()
        self.transactions: List[Dict] = []
    
    def add_position(self, position: Position) -> None:
        """Add or update a position in the portfolio."""
        symbol = position.instrument.symbol
        if symbol in self.positions:
            # Merge positions
            existing = self.positions[symbol]
            total_cost = existing.cost_basis + position.cost_basis
            total_quantity = existing.quantity + position.quantity
            existing.quantity = total_quantity
            existing.average_cost = total_cost / total_quantity if total_quantity > 0 else 0
        else:
            self.positions[symbol] = position
    
    def remove_position(self, symbol: str, quantity: float) -> float:
        """Remove quantity from position and return realized P&L."""
        if symbol not in self.positions:
            raise ValueError(f"No position found for {symbol}")
        
        position = self.positions[symbol]
        realized_pnl = position.remove_shares(quantity)
        
        # Remove position if quantity becomes zero
        if position.quantity == 0:
            del self.positions[symbol]
        
        return realized_pnl
    
    @property
    def total_value(self) -> float:
        """Calculate total portfolio value including cash."""
        positions_value = sum(pos.current_value for pos in self.positions.values())
        return positions_value + self.cash
    
    @property
    def total_cost_basis(self) -> float:
        """Calculate total cost basis of all positions."""
        return sum(pos.cost_basis for pos in self.positions.values())
    
    @property
    def unrealized_pnl(self) -> float:
        """Calculate total unrealized P&L."""
        return sum(pos.unrealized_pnl for pos in self.positions.values())
    
    @property
    def unrealized_pnl_percent(self) -> float:
        """Calculate total unrealized P&L percentage."""
        if self.total_cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.total_cost_basis) * 100
    
    def get_asset_allocation(self) -> Dict[AssetClass, float]:
        """Get asset allocation by asset class."""
        allocation = {}
        total_value = self.total_value
        
        if total_value == 0:
            return allocation
        
        # Group positions by asset class
        for position in self.positions.values():
            asset_class = position.instrument.asset_class
            value = position.current_value
            
            if asset_class in allocation:
                allocation[asset_class] += value
            else:
                allocation[asset_class] = value
        
        # Add cash
        if self.cash > 0:
            allocation[AssetClass.CASH] = self.cash
        
        # Convert to percentages
        return {k: (v / total_value) * 100 for k, v in allocation.items()}
    
    def get_sector_allocation(self) -> Dict[str, float]:
        """Get sector allocation for equity positions."""
        sector_values = {}
        total_equity_value = 0
        
        for position in self.positions.values():
            if isinstance(position.instrument, Stock):
                sector = position.instrument.sector or "Unknown"
                value = position.current_value
                
                if sector in sector_values:
                    sector_values[sector] += value
                else:
                    sector_values[sector] = value
                
                total_equity_value += value
        
        if total_equity_value == 0:
            return {}
        
        return {k: (v / total_equity_value) * 100 for k, v in sector_values.items()}
    
    def calculate_performance_metrics(self, benchmark_returns: Optional[List[float]] = None) -> PerformanceMetrics:
        """Calculate portfolio performance metrics."""
        # This is a simplified implementation
        # In practice, you'd need historical price data
        
        current_value = self.total_value
        initial_value = self.total_cost_basis + sum(t.get('amount', 0) for t in self.transactions if t.get('type') == 'deposit')
        
        if initial_value == 0:
            return PerformanceMetrics(0, 0, 0, 0, 0, 0)
        
        total_return = (current_value - initial_value) / initial_value
        
        # Placeholder calculations - would need historical data for accurate metrics
        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=total_return,  # Simplified
            volatility=0.15,  # Placeholder
            sharpe_ratio=1.2,  # Placeholder
            max_drawdown=0.08,  # Placeholder
            var_95=0.05,  # Placeholder
            beta=1.0 if benchmark_returns else None
        )


class PortfolioOptimizer:
    """Portfolio optimization using Modern Portfolio Theory."""
    
    @staticmethod
    def calculate_efficient_frontier(expected_returns: np.ndarray, 
                                   covariance_matrix: np.ndarray,
                                   num_portfolios: int = 10000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate efficient frontier using Monte Carlo simulation.
        
        Args:
            expected_returns: Expected returns for each asset
            covariance_matrix: Covariance matrix of asset returns
            num_portfolios: Number of random portfolios to generate
            
        Returns:
            Tuple of (returns, volatilities) for efficient portfolios
        """
        num_assets = len(expected_returns)
        results = np.zeros((3, num_portfolios))
        
        np.random.seed(42)  # For reproducibility
        
        for i in range(num_portfolios):
            # Generate random weights
            weights = np.random.random(num_assets)
            weights /= np.sum(weights)  # Normalize to sum to 1
            
            # Calculate portfolio return and volatility
            portfolio_return = np.dot(weights, expected_returns)
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(covariance_matrix, weights)))
            
            # Calculate Sharpe ratio (assuming risk-free rate of 0.02)
            sharpe_ratio = (portfolio_return - 0.02) / portfolio_volatility
            
            results[0, i] = portfolio_return
            results[1, i] = portfolio_volatility
            results[2, i] = sharpe_ratio
        
        return results[0], results[1]
    
    @staticmethod
    def optimize_portfolio(expected_returns: np.ndarray, 
                          covariance_matrix: np.ndarray,
                          risk_tolerance: float = 0.5) -> np.ndarray:
        """
        Optimize portfolio weights based on risk tolerance.
        
        Args:
            expected_returns: Expected returns for each asset
            covariance_matrix: Covariance matrix of asset returns
            risk_tolerance: Risk tolerance (0 = risk-averse, 1 = risk-seeking)
            
        Returns:
            Optimal portfolio weights
        """
        # Simplified optimization - in practice, use scipy.optimize
        num_assets = len(expected_returns)
        
        if risk_tolerance < 0.3:
            # Conservative: Equal weights with bias toward lower volatility
            volatilities = np.sqrt(np.diag(covariance_matrix))
            inv_vol = 1 / volatilities
            weights = inv_vol / np.sum(inv_vol)
        elif risk_tolerance > 0.7:
            # Aggressive: Weights proportional to expected returns
            weights = expected_returns / np.sum(expected_returns)
            weights = np.maximum(weights, 0)  # No short selling
        else:
            # Moderate: Equal weights
            weights = np.ones(num_assets) / num_assets
        
        return weights