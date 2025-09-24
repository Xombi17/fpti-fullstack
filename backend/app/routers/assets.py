"""
Asset management API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models import Asset, AssetType

router = APIRouter()

class AssetCreate(BaseModel):
    symbol: str
    name: str
    asset_type: str
    currency: str = "USD"
    exchange: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None

class AssetResponse(BaseModel):
    id: int
    symbol: str
    name: str
    asset_type: str
    currency: str
    exchange: Optional[str]
    sector: Optional[str]
    industry: Optional[str]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

@router.get("/", response_model=List[AssetResponse])
async def get_assets(
    asset_type: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get assets with optional filtering."""
    query = db.query(Asset).filter(Asset.is_active == True)
    
    if asset_type:
        try:
            asset_type_enum = AssetType(asset_type)
            query = query.filter(Asset.asset_type == asset_type_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid asset type: {asset_type}"
            )
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Asset.symbol.ilike(search_filter)) |
            (Asset.name.ilike(search_filter))
        )
    
    assets = query.offset(skip).limit(limit).all()
    return assets

@router.post("/", response_model=AssetResponse)
async def create_asset(
    asset: AssetCreate,
    db: Session = Depends(get_db)
):
    """Create a new asset."""
    # Check if asset already exists
    existing = db.query(Asset).filter(Asset.symbol == asset.symbol).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Asset with symbol {asset.symbol} already exists"
        )
    
    try:
        asset_type_enum = AssetType(asset.asset_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid asset type: {asset.asset_type}"
        )
    
    db_asset = Asset(
        symbol=asset.symbol,
        name=asset.name,
        asset_type=asset_type_enum,
        currency=asset.currency,
        exchange=asset.exchange,
        sector=asset.sector,
        industry=asset.industry,
        description=asset.description
    )
    
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific asset."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    return asset

@router.get("/symbol/{symbol}", response_model=AssetResponse)
async def get_asset_by_symbol(
    symbol: str,
    db: Session = Depends(get_db)
):
    """Get asset by symbol."""
    asset = db.query(Asset).filter(Asset.symbol == symbol).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset with symbol {symbol} not found"
        )
    
    return asset

@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: int,
    asset_update: AssetCreate,
    db: Session = Depends(get_db)
):
    """Update an asset."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    # Check if new symbol conflicts with existing asset
    if asset_update.symbol != asset.symbol:
        existing = db.query(Asset).filter(
            Asset.symbol == asset_update.symbol,
            Asset.id != asset_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Asset with symbol {asset_update.symbol} already exists"
            )
    
    try:
        asset_type_enum = AssetType(asset_update.asset_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid asset type: {asset_update.asset_type}"
        )
    
    # Update fields
    asset.symbol = asset_update.symbol
    asset.name = asset_update.name
    asset.asset_type = asset_type_enum
    asset.currency = asset_update.currency
    asset.exchange = asset_update.exchange
    asset.sector = asset_update.sector
    asset.industry = asset_update.industry
    asset.description = asset_update.description
    
    db.commit()
    db.refresh(asset)
    return asset

@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db)
):
    """Delete an asset (soft delete)."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    asset.is_active = False
    db.commit()
    
    return {"message": "Asset deleted successfully"}