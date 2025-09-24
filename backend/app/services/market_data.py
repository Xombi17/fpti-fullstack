"""
Market data service for fetching real-time and historical data.
"""
import asyncio
import aiohttp
import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from ..core.config import settings
from ..models import Asset, PriceHistory
from sqlalchemy.orm import Session

class MarketDataService:
    """Service for fetching market data from various providers."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = asyncio.Semaphore(settings.api_rate_limit_per_minute)
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            
        Returns:
            Current price or None if not found
        """
        if settings.market_data_provider == "yahoo":
            return await self._get_yahoo_current_price(symbol)
        elif settings.market_data_provider == "alpha_vantage":
            return await self._get_alpha_vantage_current_price(symbol)
        else:
            raise ValueError(f"Unsupported market data provider: {settings.market_data_provider}")
    
    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """
        Get current prices for multiple symbols concurrently.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbols to prices
        """
        async with self.rate_limiter:
            tasks = [self.get_current_price(symbol) for symbol in symbols]
            prices = await asyncio.gather(*tasks, return_exceptions=True)
            
            result = {}
            for symbol, price in zip(symbols, prices):
                if isinstance(price, Exception):
                    result[symbol] = None
                else:
                    result[symbol] = price
            
            return result
    
    async def get_historical_data(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """
        Get historical price data.
        
        Args:
            symbol: Stock symbol
            period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            
        Returns:
            DataFrame with historical price data
        """
        if settings.market_data_provider == "yahoo":
            return await self._get_yahoo_historical_data(symbol, period)
        else:
            raise ValueError(f"Historical data not supported for provider: {settings.market_data_provider}")
    
    async def _get_yahoo_current_price(self, symbol: str) -> Optional[float]:
        """Get current price from Yahoo Finance."""
        try:
            # Using yfinance in async context
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, symbol)
            info = await loop.run_in_executor(None, ticker.info.get, 'regularMarketPrice')
            
            if info:
                return float(info)
            
            # Fallback to fast_info
            fast_info = await loop.run_in_executor(None, lambda: ticker.fast_info)
            return float(fast_info.get('lastPrice', 0))
            
        except Exception as e:
            print(f"Error fetching Yahoo price for {symbol}: {e}")
            return None
    
    async def _get_yahoo_historical_data(self, symbol: str, period: str) -> pd.DataFrame:
        """Get historical data from Yahoo Finance."""
        try:
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, symbol)
            hist = await loop.run_in_executor(None, ticker.history, period)
            return hist
        except Exception as e:
            print(f"Error fetching Yahoo historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    async def _get_alpha_vantage_current_price(self, symbol: str) -> Optional[float]:
        """Get current price from Alpha Vantage."""
        if not settings.alpha_vantage_api_key:
            raise ValueError("Alpha Vantage API key not configured")
        
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": settings.alpha_vantage_api_key
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    global_quote = data.get("Global Quote", {})
                    price_str = global_quote.get("05. price")
                    if price_str:
                        return float(price_str)
        except Exception as e:
            print(f"Error fetching Alpha Vantage price for {symbol}: {e}")
        
        return None
    
    async def update_asset_prices(self, db: Session, asset_ids: Optional[List[int]] = None):
        """
        Update current prices for assets in the database.
        
        Args:
            db: Database session
            asset_ids: Optional list of asset IDs to update. If None, updates all active assets.
        """
        query = db.query(Asset).filter(Asset.is_active == True)
        if asset_ids:
            query = query.filter(Asset.id.in_(asset_ids))
        
        assets = query.all()
        symbols = [asset.symbol for asset in assets]
        
        if not symbols:
            return
        
        # Get current prices
        prices = await self.get_multiple_prices(symbols)
        
        # Update price history
        for asset in assets:
            price = prices.get(asset.symbol)
            if price is not None:
                # Create price history entry
                price_entry = PriceHistory(
                    asset_id=asset.id,
                    date=datetime.now(),
                    close_price=price
                )
                db.add(price_entry)
        
        db.commit()
    
    async def get_market_summary(self) -> Dict[str, float]:
        """Get major market indices summary."""
        indices = {
            "S&P 500": "^GSPC",
            "NASDAQ": "^IXIC",
            "Dow Jones": "^DJI",
            "Russell 2000": "^RUT",
            "VIX": "^VIX"
        }
        
        prices = await self.get_multiple_prices(list(indices.values()))
        
        return {name: prices.get(symbol) for name, symbol in indices.items()}


class MarketDataCache:
    """Simple in-memory cache for market data."""
    
    def __init__(self, ttl_seconds: int = 300):  # 5 minutes default TTL
        self.cache: Dict[str, Dict] = {}
        self.ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[float]:
        """Get cached price."""
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now().timestamp() - entry["timestamp"] < self.ttl:
                return entry["price"]
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, price: float):
        """Cache a price."""
        self.cache[key] = {
            "price": price,
            "timestamp": datetime.now().timestamp()
        }
    
    def clear(self):
        """Clear the cache."""
        self.cache.clear()

# Global cache instance
market_cache = MarketDataCache()