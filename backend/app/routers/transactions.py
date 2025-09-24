"""
Transaction management API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models import Transaction, Portfolio, Asset, Holding, TransactionType

router = APIRouter()

class TransactionCreate(BaseModel):
    portfolio_id: int
    asset_id: Optional[int] = None
    transaction_type: str
    quantity: float = 0.0
    price: float = 0.0
    total_amount: float
    fees: float = 0.0
    currency: str = "USD"
    transaction_date: datetime
    description: Optional[str] = None

class TransactionResponse(BaseModel):
    id: int
    portfolio_id: int
    asset_id: Optional[int]
    transaction_type: str
    quantity: float
    price: float
    total_amount: float
    fees: float
    currency: str
    transaction_date: datetime
    description: Optional[str]
    created_at: datetime
    
    class Config:
        orm_mode = True

@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    portfolio_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Get transactions, optionally filtered by portfolio."""
    query = db.query(Transaction)
    
    if portfolio_id:
        # Verify portfolio belongs to user
        portfolio = db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == user_id
        ).first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
        
        query = query.filter(Transaction.portfolio_id == portfolio_id)
    else:
        # Get all transactions for user's portfolios
        user_portfolio_ids = db.query(Portfolio.id).filter(
            Portfolio.user_id == user_id
        ).subquery()
        query = query.filter(Transaction.portfolio_id.in_(user_portfolio_ids))
    
    transactions = query.order_by(Transaction.transaction_date.desc()).offset(skip).limit(limit).all()
    return transactions

@router.post("/", response_model=TransactionResponse)
async def create_transaction(
    transaction: TransactionCreate,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Create a new transaction and update holdings."""
    # Verify portfolio belongs to user
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == transaction.portfolio_id,
        Portfolio.user_id == user_id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Verify asset exists if provided
    if transaction.asset_id:
        asset = db.query(Asset).filter(Asset.id == transaction.asset_id).first()
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
    
    # Create transaction
    db_transaction = Transaction(
        portfolio_id=transaction.portfolio_id,
        asset_id=transaction.asset_id,
        transaction_type=TransactionType(transaction.transaction_type),
        quantity=transaction.quantity,
        price=transaction.price,
        total_amount=transaction.total_amount,
        fees=transaction.fees,
        currency=transaction.currency,
        transaction_date=transaction.transaction_date,
        description=transaction.description
    )
    
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    # Update holdings if it's a buy/sell transaction
    if transaction.asset_id and transaction.transaction_type in ["buy", "sell"]:
        await update_holding(
            db, transaction.portfolio_id, transaction.asset_id,
            transaction.transaction_type, transaction.quantity, transaction.price
        )
    
    return db_transaction

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Get a specific transaction."""
    # Get transaction and verify user owns the portfolio
    transaction = db.query(Transaction).join(Portfolio).filter(
        Transaction.id == transaction_id,
        Portfolio.user_id == user_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return transaction

@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    user_id: int = 1,  # Simplified - would come from authentication
    db: Session = Depends(get_db)
):
    """Delete a transaction and reverse its effects on holdings."""
    # Get transaction and verify user owns the portfolio
    transaction = db.query(Transaction).join(Portfolio).filter(
        Transaction.id == transaction_id,
        Portfolio.user_id == user_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Reverse the transaction effects on holdings
    if transaction.asset_id and transaction.transaction_type in [TransactionType.BUY, TransactionType.SELL]:
        reverse_type = "sell" if transaction.transaction_type == TransactionType.BUY else "buy"
        await update_holding(
            db, transaction.portfolio_id, transaction.asset_id,
            reverse_type, transaction.quantity, transaction.price
        )
    
    # Delete the transaction
    db.delete(transaction)
    db.commit()
    
    return {"message": "Transaction deleted successfully"}

async def update_holding(db: Session, portfolio_id: int, asset_id: int,
                        transaction_type: str, quantity: float, price: float):
    """Update holding based on transaction."""
    holding = db.query(Holding).filter(
        Holding.portfolio_id == portfolio_id,
        Holding.asset_id == asset_id
    ).first()
    
    if transaction_type == "buy":
        if holding:
            # Update existing holding
            total_cost = (holding.quantity * holding.average_cost) + (quantity * price)
            holding.quantity += quantity
            holding.average_cost = total_cost / holding.quantity if holding.quantity > 0 else 0
        else:
            # Create new holding
            holding = Holding(
                portfolio_id=portfolio_id,
                asset_id=asset_id,
                quantity=quantity,
                average_cost=price,
                current_value=quantity * price  # Will be updated by market data
            )
            db.add(holding)
    
    elif transaction_type == "sell":
        if not holding or holding.quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient shares to sell"
            )
        
        holding.quantity -= quantity
        
        # Remove holding if quantity becomes zero
        if holding.quantity == 0:
            db.delete(holding)
    
    db.commit()