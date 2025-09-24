"""
Portfolio management API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models import Portfolio, User, Holding, Asset
from ..core.financial_models import Portfolio as PortfolioModel

router = APIRouter()

class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None

class PortfolioResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    user_id: int
    is_active: bool
    created_at: datetime
    total_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    
    class Config:
        orm_mode = True

class PortfolioValue(BaseModel):
    portfolio_id: int
    total_value: float
    cash_value: float
    positions_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    last_updated: datetime

class AssetAllocation(BaseModel):
    asset_class: str
    percentage: float
    value: float

class PortfolioAllocation(BaseModel):
    portfolio_id: int
    allocations: List[AssetAllocation]
    last_updated: datetime

@router.get("/", response_model=List[PortfolioResponse])
async def get_portfolios(
    skip: int = 0,
    limit: int = 100,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Get all portfolios for a user."""
    portfolios = db.query(Portfolio).filter(
        Portfolio.user_id == user_id,
        Portfolio.is_active == True
    ).offset(skip).limit(limit).all()
    
    return portfolios

@router.post("/", response_model=PortfolioResponse)
async def create_portfolio(
    portfolio: PortfolioCreate,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Create a new portfolio."""
    db_portfolio = Portfolio(
        name=portfolio.name,
        description=portfolio.description,
        user_id=user_id
    )
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio

@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: int,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Get a specific portfolio."""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == user_id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    return portfolio

@router.get("/{portfolio_id}/value", response_model=PortfolioValue)
async def get_portfolio_value(
    portfolio_id: int,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Get current portfolio value and P&L."""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == user_id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Get all holdings for the portfolio
    holdings = db.query(Holding).filter(Holding.portfolio_id == portfolio_id).all()
    
    total_value = sum(holding.current_value for holding in holdings)
    positions_value = total_value
    cash_value = 0.0  # Simplified - would track cash separately
    
    # Calculate unrealized P&L
    total_cost = sum(holding.quantity * holding.average_cost for holding in holdings)
    unrealized_pnl = total_value - total_cost
    unrealized_pnl_percent = (unrealized_pnl / total_cost * 100) if total_cost > 0 else 0
    
    return PortfolioValue(
        portfolio_id=portfolio_id,
        total_value=total_value,
        cash_value=cash_value,
        positions_value=positions_value,
        unrealized_pnl=unrealized_pnl,
        unrealized_pnl_percent=unrealized_pnl_percent,
        last_updated=datetime.now()
    )

@router.get("/{portfolio_id}/allocation", response_model=PortfolioAllocation)
async def get_portfolio_allocation(
    portfolio_id: int,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Get portfolio asset allocation."""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == user_id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Get holdings with asset information
    holdings_query = db.query(Holding, Asset).join(Asset).filter(
        Holding.portfolio_id == portfolio_id,
        Holding.quantity > 0
    ).all()
    
    total_value = sum(holding.current_value for holding, asset in holdings_query)
    
    # Group by asset type
    allocation_dict = {}
    for holding, asset in holdings_query:
        asset_type = asset.asset_type.value
        value = holding.current_value
        
        if asset_type in allocation_dict:
            allocation_dict[asset_type] += value
        else:
            allocation_dict[asset_type] = value
    
    # Convert to percentages and create response
    allocations = []
    for asset_type, value in allocation_dict.items():
        percentage = (value / total_value * 100) if total_value > 0 else 0
        allocations.append(AssetAllocation(
            asset_class=asset_type,
            percentage=percentage,
            value=value
        ))
    
    return PortfolioAllocation(
        portfolio_id=portfolio_id,
        allocations=allocations,
        last_updated=datetime.now()
    )

@router.delete("/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: int,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Delete a portfolio (soft delete)."""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == user_id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    portfolio.is_active = False
    db.commit()
    
    return {"message": "Portfolio deleted successfully"}