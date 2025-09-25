"""
Net Worth management API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from decimal import Decimal

from ..database import get_db
from ..models import (
    NetWorthAsset, NetWorthLiability, NetWorthSnapshot, Portfolio, Holding,
    NetWorthAssetType, NetWorthLiabilityType, User
)

router = APIRouter()

# Pydantic Models
class NetWorthAssetCreate(BaseModel):
    name: str
    asset_type: str
    current_value: float
    description: Optional[str] = None

class NetWorthAssetUpdate(BaseModel):
    name: Optional[str] = None
    current_value: Optional[float] = None
    description: Optional[str] = None

class NetWorthAssetResponse(BaseModel):
    id: int
    name: str
    asset_type: str
    current_value: float
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class NetWorthLiabilityCreate(BaseModel):
    name: str
    liability_type: str
    current_balance: float
    interest_rate: float = 0.0
    minimum_payment: float = 0.0
    description: Optional[str] = None

class NetWorthLiabilityUpdate(BaseModel):
    name: Optional[str] = None
    current_balance: Optional[float] = None
    interest_rate: Optional[float] = None
    minimum_payment: Optional[float] = None
    description: Optional[str] = None

class NetWorthLiabilityResponse(BaseModel):
    id: int
    name: str
    liability_type: str
    current_balance: float
    interest_rate: float
    minimum_payment: float
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class NetWorthSummary(BaseModel):
    total_assets: float
    total_liabilities: float
    net_worth: float
    portfolio_value: float
    real_estate_value: float
    cash_savings_value: float
    other_assets_value: float
    last_updated: datetime

class NetWorthSnapshotResponse(BaseModel):
    id: int
    date: datetime
    total_assets: float
    total_liabilities: float
    net_worth: float
    portfolio_value: float
    cash_value: float
    real_estate_value: float
    other_assets_value: float
    created_at: datetime
    
    class Config:
        from_attributes = True

# Asset Endpoints
@router.get("/assets/", response_model=List[NetWorthAssetResponse])
async def get_net_worth_assets(
    skip: int = 0,
    limit: int = 100,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Get all net worth assets for a user."""
    assets = db.query(NetWorthAsset).filter(
        NetWorthAsset.user_id == user_id,
        NetWorthAsset.is_active == True
    ).offset(skip).limit(limit).all()
    
    return assets

@router.post("/assets/", response_model=NetWorthAssetResponse)
async def create_net_worth_asset(
    asset: NetWorthAssetCreate,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Create a new net worth asset."""
    try:
        asset_type_enum = NetWorthAssetType(asset.asset_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid asset type: {asset.asset_type}"
        )
    
    db_asset = NetWorthAsset(
        user_id=user_id,
        name=asset.name,
        asset_type=asset_type_enum,
        current_value=asset.current_value,
        description=asset.description
    )
    
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

@router.get("/assets/{asset_id}", response_model=NetWorthAssetResponse)
async def get_net_worth_asset(
    asset_id: int,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Get a specific net worth asset."""
    asset = db.query(NetWorthAsset).filter(
        NetWorthAsset.id == asset_id,
        NetWorthAsset.user_id == user_id
    ).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    return asset

@router.put("/assets/{asset_id}", response_model=NetWorthAssetResponse)
async def update_net_worth_asset(
    asset_id: int,
    asset_update: NetWorthAssetUpdate,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Update a net worth asset."""
    asset = db.query(NetWorthAsset).filter(
        NetWorthAsset.id == asset_id,
        NetWorthAsset.user_id == user_id
    ).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    # Update fields if provided
    if asset_update.name is not None:
        asset.name = asset_update.name
    if asset_update.current_value is not None:
        asset.current_value = asset_update.current_value
    if asset_update.description is not None:
        asset.description = asset_update.description
    
    asset.updated_at = datetime.now()
    db.commit()
    db.refresh(asset)
    return asset

@router.delete("/assets/{asset_id}")
async def delete_net_worth_asset(
    asset_id: int,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Delete (deactivate) a net worth asset."""
    asset = db.query(NetWorthAsset).filter(
        NetWorthAsset.id == asset_id,
        NetWorthAsset.user_id == user_id
    ).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    asset.is_active = False
    asset.updated_at = datetime.now()
    db.commit()
    
    return {"message": "Asset deleted successfully"}

# Liability Endpoints
@router.get("/liabilities/", response_model=List[NetWorthLiabilityResponse])
async def get_net_worth_liabilities(
    skip: int = 0,
    limit: int = 100,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Get all net worth liabilities for a user."""
    liabilities = db.query(NetWorthLiability).filter(
        NetWorthLiability.user_id == user_id,
        NetWorthLiability.is_active == True
    ).offset(skip).limit(limit).all()
    
    return liabilities

@router.post("/liabilities/", response_model=NetWorthLiabilityResponse)
async def create_net_worth_liability(
    liability: NetWorthLiabilityCreate,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Create a new net worth liability."""
    try:
        liability_type_enum = NetWorthLiabilityType(liability.liability_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid liability type: {liability.liability_type}"
        )
    
    db_liability = NetWorthLiability(
        user_id=user_id,
        name=liability.name,
        liability_type=liability_type_enum,
        current_balance=liability.current_balance,
        interest_rate=liability.interest_rate,
        minimum_payment=liability.minimum_payment,
        description=liability.description
    )
    
    db.add(db_liability)
    db.commit()
    db.refresh(db_liability)
    return db_liability

@router.get("/liabilities/{liability_id}", response_model=NetWorthLiabilityResponse)
async def get_net_worth_liability(
    liability_id: int,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Get a specific net worth liability."""
    liability = db.query(NetWorthLiability).filter(
        NetWorthLiability.id == liability_id,
        NetWorthLiability.user_id == user_id
    ).first()
    
    if not liability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Liability not found"
        )
    
    return liability

@router.put("/liabilities/{liability_id}", response_model=NetWorthLiabilityResponse)
async def update_net_worth_liability(
    liability_id: int,
    liability_update: NetWorthLiabilityUpdate,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Update a net worth liability."""
    liability = db.query(NetWorthLiability).filter(
        NetWorthLiability.id == liability_id,
        NetWorthLiability.user_id == user_id
    ).first()
    
    if not liability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Liability not found"
        )
    
    # Update fields if provided
    if liability_update.name is not None:
        liability.name = liability_update.name
    if liability_update.current_balance is not None:
        liability.current_balance = liability_update.current_balance
    if liability_update.interest_rate is not None:
        liability.interest_rate = liability_update.interest_rate
    if liability_update.minimum_payment is not None:
        liability.minimum_payment = liability_update.minimum_payment
    if liability_update.description is not None:
        liability.description = liability_update.description
    
    liability.updated_at = datetime.now()
    db.commit()
    db.refresh(liability)
    return liability

@router.delete("/liabilities/{liability_id}")
async def delete_net_worth_liability(
    liability_id: int,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Delete (deactivate) a net worth liability."""
    liability = db.query(NetWorthLiability).filter(
        NetWorthLiability.id == liability_id,
        NetWorthLiability.user_id == user_id
    ).first()
    
    if not liability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Liability not found"
        )
    
    liability.is_active = False
    liability.updated_at = datetime.now()
    db.commit()
    
    return {"message": "Liability deleted successfully"}

# Net Worth Summary and Snapshots
@router.get("/summary", response_model=NetWorthSummary)
async def get_net_worth_summary(
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Get current net worth summary."""
    # Calculate portfolio value
    portfolios = db.query(Portfolio).filter(
        Portfolio.user_id == user_id,
        Portfolio.is_active == True
    ).all()
    
    portfolio_value = 0.0
    for portfolio in portfolios:
        holdings = db.query(Holding).filter(Holding.portfolio_id == portfolio.id).all()
        portfolio_value += sum(holding.current_value for holding in holdings)
    
    # Get net worth assets
    assets = db.query(NetWorthAsset).filter(
        NetWorthAsset.user_id == user_id,
        NetWorthAsset.is_active == True
    ).all()
    
    # Calculate asset values by type
    real_estate_value = sum(a.current_value for a in assets if a.asset_type == NetWorthAssetType.REAL_ESTATE)
    cash_savings_value = sum(a.current_value for a in assets if a.asset_type == NetWorthAssetType.CASH_SAVINGS)
    other_assets_value = sum(a.current_value for a in assets if a.asset_type not in [NetWorthAssetType.REAL_ESTATE, NetWorthAssetType.CASH_SAVINGS])
    
    total_assets = portfolio_value + sum(a.current_value for a in assets)
    
    # Get liabilities
    liabilities = db.query(NetWorthLiability).filter(
        NetWorthLiability.user_id == user_id,
        NetWorthLiability.is_active == True
    ).all()
    
    total_liabilities = sum(l.current_balance for l in liabilities)
    net_worth = total_assets - total_liabilities
    
    return NetWorthSummary(
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        net_worth=net_worth,
        portfolio_value=portfolio_value,
        real_estate_value=real_estate_value,
        cash_savings_value=cash_savings_value,
        other_assets_value=other_assets_value,
        last_updated=datetime.now()
    )

@router.post("/snapshot")
async def create_net_worth_snapshot(
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Create a net worth snapshot."""
    # Get current summary
    summary = await get_net_worth_summary(user_id, db)
    
    # Create snapshot
    snapshot = NetWorthSnapshot(
        user_id=user_id,
        date=datetime.now(),
        total_assets=summary.total_assets,
        total_liabilities=summary.total_liabilities,
        net_worth=summary.net_worth,
        portfolio_value=summary.portfolio_value,
        cash_value=summary.cash_savings_value,
        real_estate_value=summary.real_estate_value,
        other_assets_value=summary.other_assets_value
    )
    
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    
    return {"message": "Net worth snapshot created successfully", "snapshot_id": snapshot.id}

@router.get("/snapshots", response_model=List[NetWorthSnapshotResponse])
async def get_net_worth_snapshots(
    days: int = 365,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Get net worth snapshots for trend analysis."""
    start_date = datetime.now() - timedelta(days=days)
    
    snapshots = db.query(NetWorthSnapshot).filter(
        NetWorthSnapshot.user_id == user_id,
        NetWorthSnapshot.date >= start_date
    ).order_by(NetWorthSnapshot.date.desc()).all()
    
    return snapshots