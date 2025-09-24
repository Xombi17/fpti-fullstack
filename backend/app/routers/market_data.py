"""
Market data API endpoints.
"""
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..services.market_data import MarketDataService, market_cache
from ..models import Asset, PriceHistory

router = APIRouter()

class PriceResponse(BaseModel):
    symbol: str
    price: float
    timestamp: datetime

class HistoricalDataResponse(BaseModel):
    symbol: str
    data: List[Dict]
    period: str

class MarketSummaryResponse(BaseModel):
    indices: Dict[str, Optional[float]]
    last_updated: datetime

@router.get("/price/{symbol}", response_model=PriceResponse)
async def get_current_price(symbol: str):
    """Get current price for a symbol."""
    # Check cache first
    cached_price = market_cache.get(symbol)
    if cached_price is not None:
        return PriceResponse(
            symbol=symbol,
            price=cached_price,
            timestamp=datetime.now()
        )
    
    # Fetch from market data service
    async with MarketDataService() as service:
        price = await service.get_current_price(symbol)
        
        if price is None:
            raise HTTPException(
                status_code=404,
                detail=f"Price not found for symbol {symbol}"
            )
        
        # Cache the result
        market_cache.set(symbol, price)
        
        return PriceResponse(
            symbol=symbol,
            price=price,
            timestamp=datetime.now()
        )

@router.post("/prices", response_model=List[PriceResponse])
async def get_multiple_prices(symbols: List[str]):
    """Get current prices for multiple symbols."""
    # Check cache for all symbols
    cached_results = []
    missing_symbols = []
    
    for symbol in symbols:
        cached_price = market_cache.get(symbol)
        if cached_price is not None:
            cached_results.append(PriceResponse(
                symbol=symbol,
                price=cached_price,
                timestamp=datetime.now()
            ))
        else:
            missing_symbols.append(symbol)
    
    # Fetch missing prices
    if missing_symbols:
        async with MarketDataService() as service:
            prices = await service.get_multiple_prices(missing_symbols)
            
            for symbol, price in prices.items():
                if price is not None:
                    market_cache.set(symbol, price)
                    cached_results.append(PriceResponse(
                        symbol=symbol,
                        price=price,
                        timestamp=datetime.now()
                    ))
    
    return cached_results

@router.get("/historical/{symbol}", response_model=HistoricalDataResponse)
async def get_historical_data(symbol: str, period: str = "1y"):
    """Get historical price data for a symbol."""
    valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
    if period not in valid_periods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}"
        )
    
    async with MarketDataService() as service:
        df = await service.get_historical_data(symbol, period)
        
        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Historical data not found for symbol {symbol}"
            )
        
        # Convert DataFrame to list of dictionaries
        data = []
        for date, row in df.iterrows():
            data.append({
                "date": date.isoformat(),
                "open": row.get('Open', 0),
                "high": row.get('High', 0),
                "low": row.get('Low', 0),
                "close": row.get('Close', 0),
                "volume": row.get('Volume', 0)
            })
        
        return HistoricalDataResponse(
            symbol=symbol,
            data=data,
            period=period
        )

@router.get("/summary", response_model=MarketSummaryResponse)
async def get_market_summary():
    """Get summary of major market indices."""
    async with MarketDataService() as service:
        indices = await service.get_market_summary()
        
        return MarketSummaryResponse(
            indices=indices,
            last_updated=datetime.now()
        )

@router.post("/update-prices")
async def update_asset_prices(
    background_tasks: BackgroundTasks,
    asset_ids: Optional[List[int]] = None,
    db: Session = Depends(get_db)
):
    """Update current prices for assets in the database."""
    async def update_prices_task():
        async with MarketDataService() as service:
            await service.update_asset_prices(db, asset_ids)
    
    background_tasks.add_task(update_prices_task)
    
    return {"message": "Price update initiated"}

@router.get("/price-history/{asset_id}")
async def get_asset_price_history(
    asset_id: int,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get price history for an asset from the database."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )
    
    price_history = db.query(PriceHistory).filter(
        PriceHistory.asset_id == asset_id
    ).order_by(
        PriceHistory.date.desc()
    ).limit(limit).all()
    
    return {
        "asset_id": asset_id,
        "symbol": asset.symbol,
        "history": [
            {
                "date": entry.date.isoformat(),
                "open": entry.open_price,
                "high": entry.high_price,
                "low": entry.low_price,
                "close": entry.close_price,
                "volume": entry.volume
            }
            for entry in price_history
        ]
    }

@router.delete("/cache")
async def clear_price_cache():
    """Clear the price cache."""
    market_cache.clear()
    return {"message": "Price cache cleared"}