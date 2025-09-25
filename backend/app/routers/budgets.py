"""
Budget management router for FPTI application.
Provides endpoints for budget CRUD operations and spending tracking.
"""
from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, extract

from ..database import get_db
from ..models import Budget, BudgetTransaction, BudgetCategory
from pydantic import BaseModel

router = APIRouter()


# Pydantic models for request/response
class BudgetCreate(BaseModel):
    name: str
    category: BudgetCategory
    monthly_limit: float
    start_date: datetime
    end_date: Optional[datetime] = None


class BudgetUpdate(BaseModel):
    name: Optional[str] = None
    monthly_limit: Optional[float] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class BudgetResponse(BaseModel):
    id: int
    name: str
    category: BudgetCategory
    monthly_limit: float
    current_spent: float
    start_date: datetime
    end_date: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BudgetTransactionCreate(BaseModel):
    budget_id: int
    description: str
    amount: float
    transaction_date: datetime
    notes: Optional[str] = None


class BudgetTransactionUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    transaction_date: Optional[datetime] = None
    notes: Optional[str] = None


class BudgetTransactionResponse(BaseModel):
    id: int
    budget_id: int
    description: str
    amount: float
    transaction_date: datetime
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BudgetSummaryResponse(BaseModel):
    total_budget: float
    total_spent: float
    remaining_budget: float
    categories: List[dict]


# Budget CRUD endpoints
@router.post("/budgets/", response_model=BudgetResponse)
def create_budget(budget: BudgetCreate, db: Session = Depends(get_db)):
    """Create a new budget."""
    # For demo purposes, using user_id = 1
    # In production, this would come from authentication
    user_id = 1
    
    db_budget = Budget(
        user_id=user_id,
        name=budget.name,
        category=budget.category,
        monthly_limit=budget.monthly_limit,
        start_date=budget.start_date,
        end_date=budget.end_date
    )
    
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget


@router.get("/budgets/", response_model=List[BudgetResponse])
def get_budgets(
    active_only: bool = Query(True, description="Filter for active budgets only"),
    category: Optional[BudgetCategory] = Query(None, description="Filter by budget category"),
    db: Session = Depends(get_db)
):
    """Get all budgets for the user."""
    user_id = 1  # Demo user
    
    query = db.query(Budget).filter(Budget.user_id == user_id)
    
    if active_only:
        query = query.filter(Budget.is_active == True)
    
    if category:
        query = query.filter(Budget.category == category)
    
    return query.order_by(Budget.created_at.desc()).all()


@router.get("/budgets/{budget_id}", response_model=BudgetResponse)
def get_budget(budget_id: int, db: Session = Depends(get_db)):
    """Get a specific budget by ID."""
    user_id = 1  # Demo user
    
    budget = db.query(Budget).filter(
        and_(Budget.id == budget_id, Budget.user_id == user_id)
    ).first()
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    return budget


@router.put("/budgets/{budget_id}", response_model=BudgetResponse)
def update_budget(budget_id: int, budget_update: BudgetUpdate, db: Session = Depends(get_db)):
    """Update a budget."""
    user_id = 1  # Demo user
    
    budget = db.query(Budget).filter(
        and_(Budget.id == budget_id, Budget.user_id == user_id)
    ).first()
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    update_data = budget_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(budget, field, value)
    
    db.commit()
    db.refresh(budget)
    return budget


@router.delete("/budgets/{budget_id}")
def delete_budget(budget_id: int, db: Session = Depends(get_db)):
    """Delete a budget."""
    user_id = 1  # Demo user
    
    budget = db.query(Budget).filter(
        and_(Budget.id == budget_id, Budget.user_id == user_id)
    ).first()
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    db.delete(budget)
    db.commit()
    return {"message": "Budget deleted successfully"}


# Budget Transaction endpoints
@router.post("/budget-transactions/", response_model=BudgetTransactionResponse)
def create_budget_transaction(transaction: BudgetTransactionCreate, db: Session = Depends(get_db)):
    """Create a new budget transaction."""
    user_id = 1  # Demo user
    
    # Verify budget exists and belongs to user
    budget = db.query(Budget).filter(
        and_(Budget.id == transaction.budget_id, Budget.user_id == user_id)
    ).first()
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    db_transaction = BudgetTransaction(
        budget_id=transaction.budget_id,
        user_id=user_id,
        description=transaction.description,
        amount=transaction.amount,
        transaction_date=transaction.transaction_date,
        notes=transaction.notes
    )
    
    db.add(db_transaction)
    
    # Update budget current_spent
    budget.current_spent += transaction.amount
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


@router.get("/budget-transactions/", response_model=List[BudgetTransactionResponse])
def get_budget_transactions(
    budget_id: Optional[int] = Query(None, description="Filter by budget ID"),
    start_date: Optional[date] = Query(None, description="Filter transactions from this date"),
    end_date: Optional[date] = Query(None, description="Filter transactions until this date"),
    limit: int = Query(100, description="Maximum number of transactions to return"),
    db: Session = Depends(get_db)
):
    """Get budget transactions for the user."""
    user_id = 1  # Demo user
    
    query = db.query(BudgetTransaction).filter(BudgetTransaction.user_id == user_id)
    
    if budget_id:
        query = query.filter(BudgetTransaction.budget_id == budget_id)
    
    if start_date:
        query = query.filter(BudgetTransaction.transaction_date >= start_date)
    
    if end_date:
        query = query.filter(BudgetTransaction.transaction_date <= end_date)
    
    return query.order_by(BudgetTransaction.transaction_date.desc()).limit(limit).all()


@router.get("/budget-transactions/{transaction_id}", response_model=BudgetTransactionResponse)
def get_budget_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Get a specific budget transaction by ID."""
    user_id = 1  # Demo user
    
    transaction = db.query(BudgetTransaction).filter(
        and_(BudgetTransaction.id == transaction_id, BudgetTransaction.user_id == user_id)
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return transaction


@router.put("/budget-transactions/{transaction_id}", response_model=BudgetTransactionResponse)
def update_budget_transaction(
    transaction_id: int, 
    transaction_update: BudgetTransactionUpdate, 
    db: Session = Depends(get_db)
):
    """Update a budget transaction."""
    user_id = 1  # Demo user
    
    transaction = db.query(BudgetTransaction).filter(
        and_(BudgetTransaction.id == transaction_id, BudgetTransaction.user_id == user_id)
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Track old amount for budget adjustment
    old_amount = transaction.amount
    
    update_data = transaction_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(transaction, field, value)
    
    # Update budget current_spent if amount changed
    if "amount" in update_data:
        budget = db.query(Budget).filter(Budget.id == transaction.budget_id).first()
        if budget:
            budget.current_spent = budget.current_spent - old_amount + transaction.amount
    
    db.commit()
    db.refresh(transaction)
    return transaction


@router.delete("/budget-transactions/{transaction_id}")
def delete_budget_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Delete a budget transaction."""
    user_id = 1  # Demo user
    
    transaction = db.query(BudgetTransaction).filter(
        and_(BudgetTransaction.id == transaction_id, BudgetTransaction.user_id == user_id)
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Update budget current_spent
    budget = db.query(Budget).filter(Budget.id == transaction.budget_id).first()
    if budget:
        budget.current_spent -= transaction.amount
    
    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted successfully"}


# Budget Analytics endpoints
@router.get("/budgets/summary/monthly", response_model=BudgetSummaryResponse)
def get_monthly_budget_summary(
    year: int = Query(datetime.now().year, description="Year for the summary"),
    month: int = Query(datetime.now().month, description="Month for the summary"),
    db: Session = Depends(get_db)
):
    """Get monthly budget summary with spending breakdown."""
    user_id = 1  # Demo user
    
    # Get active budgets
    budgets = db.query(Budget).filter(
        and_(Budget.user_id == user_id, Budget.is_active == True)
    ).all()
    
    total_budget = sum(budget.monthly_limit for budget in budgets)
    
    # Calculate spending for the specified month
    total_spent = db.query(func.sum(BudgetTransaction.amount)).filter(
        and_(
            BudgetTransaction.user_id == user_id,
            extract('year', BudgetTransaction.transaction_date) == year,
            extract('month', BudgetTransaction.transaction_date) == month
        )
    ).scalar() or 0.0
    
    # Category breakdown
    categories = []
    for budget in budgets:
        category_spent = db.query(func.sum(BudgetTransaction.amount)).filter(
            and_(
                BudgetTransaction.budget_id == budget.id,
                extract('year', BudgetTransaction.transaction_date) == year,
                extract('month', BudgetTransaction.transaction_date) == month
            )
        ).scalar() or 0.0
        
        categories.append({
            "category": budget.category.value,
            "budget": budget.monthly_limit,
            "spent": category_spent,
            "remaining": budget.monthly_limit - category_spent,
            "percentage": (category_spent / budget.monthly_limit * 100) if budget.monthly_limit > 0 else 0
        })
    
    return BudgetSummaryResponse(
        total_budget=total_budget,
        total_spent=total_spent,
        remaining_budget=total_budget - total_spent,
        categories=categories
    )


@router.get("/budgets/categories/spending")
def get_category_spending(
    year: int = Query(datetime.now().year, description="Year for the analysis"),
    month: Optional[int] = Query(None, description="Month for the analysis (optional)"),
    db: Session = Depends(get_db)
):
    """Get spending breakdown by budget category."""
    user_id = 1  # Demo user
    
    query = db.query(
        Budget.category,
        func.sum(BudgetTransaction.amount).label("total_spent"),
        func.count(BudgetTransaction.id).label("transaction_count")
    ).join(
        BudgetTransaction, Budget.id == BudgetTransaction.budget_id
    ).filter(
        and_(
            Budget.user_id == user_id,
            extract('year', BudgetTransaction.transaction_date) == year
        )
    )
    
    if month:
        query = query.filter(extract('month', BudgetTransaction.transaction_date) == month)
    
    results = query.group_by(Budget.category).all()
    
    return [
        {
            "category": result.category.value,
            "total_spent": result.total_spent,
            "transaction_count": result.transaction_count
        }
        for result in results
    ]