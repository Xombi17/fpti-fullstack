"""
Background tasks for FPTI application.
Handles automated processes like daily net worth snapshots and budget updates.
"""
import asyncio
from datetime import datetime, date, timedelta
from typing import List
import logging
from sqlalchemy import and_, func, extract
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import User, Budget, BudgetTransaction, NetWorthAsset, NetWorthLiability

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """Manager for handling background tasks."""
    
    def __init__(self):
        self.running = False
        self.tasks = []
    
    async def start(self):
        """Start all background tasks."""
        self.running = True
        logger.info("Starting background task manager")
        
        # Schedule daily tasks
        self.tasks.append(asyncio.create_task(self._daily_task_scheduler()))
        
        # Schedule hourly tasks  
        self.tasks.append(asyncio.create_task(self._hourly_task_scheduler()))
        
        # Wait for all tasks
        await asyncio.gather(*self.tasks)
    
    async def stop(self):
        """Stop all background tasks."""
        self.running = False
        logger.info("Stopping background task manager")
        
        for task in self.tasks:
            task.cancel()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
    
    async def _daily_task_scheduler(self):
        """Schedule daily tasks."""
        while self.running:
            try:
                # Run daily tasks at midnight
                now = datetime.now()
                next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                sleep_seconds = (next_midnight - now).total_seconds()
                
                logger.info(f"Next daily task run in {sleep_seconds} seconds")
                await asyncio.sleep(sleep_seconds)
                
                if self.running:
                    await self._run_daily_tasks()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in daily task scheduler: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour
    
    async def _hourly_task_scheduler(self):
        """Schedule hourly tasks."""
        while self.running:
            try:
                # Run hourly tasks
                await asyncio.sleep(3600)  # 1 hour
                
                if self.running:
                    await self._run_hourly_tasks()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in hourly task scheduler: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes
    
    async def _run_daily_tasks(self):
        """Run all daily tasks."""
        logger.info("Running daily tasks")
        
        db = SessionLocal()
        try:
            # Create net worth snapshots for all users
            await self._create_net_worth_snapshots(db)
            
            # Reset daily budget tracking
            await self._reset_daily_budgets(db)
            
            # Clean up old data
            await self._cleanup_old_data(db)
            
        except Exception as e:
            logger.error(f"Error running daily tasks: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def _run_hourly_tasks(self):
        """Run all hourly tasks."""
        logger.info("Running hourly tasks")
        
        db = SessionLocal()
        try:
            # Update budget current_spent from transactions
            await self._update_budget_spending(db)
            
        except Exception as e:
            logger.error(f"Error running hourly tasks: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def _create_net_worth_snapshots(self, db: Session):
        """Create daily net worth snapshots for all users."""
        logger.info("Creating net worth snapshots")
        
        users = db.query(User).filter(User.is_active == True).all()
        
        for user in users:
            try:
                # Calculate total assets
                total_assets = db.query(func.sum(NetWorthAsset.current_value)).filter(
                    and_(NetWorthAsset.user_id == user.id, NetWorthAsset.is_active == True)
                ).scalar() or 0.0
                
                # Calculate total liabilities
                total_liabilities = db.query(func.sum(NetWorthLiability.current_balance)).filter(
                    and_(NetWorthLiability.user_id == user.id, NetWorthLiability.is_active == True)
                ).scalar() or 0.0
                
                net_worth = total_assets - total_liabilities
                
                logger.info(f"User {user.id} net worth: ${net_worth:,.2f} (Assets: ${total_assets:,.2f}, Liabilities: ${total_liabilities:,.2f})")
                
                # Here you would create a NetWorthSnapshot record
                # For now, just log the calculation
                
            except Exception as e:
                logger.error(f"Error creating net worth snapshot for user {user.id}: {e}")
                continue
        
        db.commit()
    
    async def _reset_daily_budgets(self, db: Session):
        """Reset daily budget tracking if needed."""
        logger.info("Checking daily budget resets")
        
        today = date.today()
        
        # This is a placeholder for daily budget reset logic
        # You might want to reset daily spending limits or create new budget periods
        
        budgets = db.query(Budget).filter(Budget.is_active == True).all()
        
        for budget in budgets:
            # Example: Reset monthly budgets at the start of each month
            if today.day == 1:  # First day of month
                budget.current_spent = 0.0
                logger.info(f"Reset monthly budget {budget.id} for user {budget.user_id}")
        
        db.commit()
    
    async def _update_budget_spending(self, db: Session):
        """Update budget current_spent from actual transactions."""
        logger.info("Updating budget spending totals")
        
        budgets = db.query(Budget).filter(Budget.is_active == True).all()
        
        for budget in budgets:
            try:
                # Calculate current month spending for this budget
                current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                total_spent = db.query(func.sum(BudgetTransaction.amount)).filter(
                    and_(
                        BudgetTransaction.budget_id == budget.id,
                        BudgetTransaction.transaction_date >= current_month
                    )
                ).scalar() or 0.0
                
                if budget.current_spent != total_spent:
                    logger.info(f"Updating budget {budget.id} spending: ${budget.current_spent:.2f} -> ${total_spent:.2f}")
                    budget.current_spent = total_spent
                
            except Exception as e:
                logger.error(f"Error updating budget {budget.id} spending: {e}")
                continue
        
        db.commit()
    
    async def _cleanup_old_data(self, db: Session):
        """Clean up old data to maintain database performance."""
        logger.info("Cleaning up old data")
        
        # Example: Remove budget transactions older than 2 years
        cutoff_date = datetime.now() - timedelta(days=730)
        
        old_transactions = db.query(BudgetTransaction).filter(
            BudgetTransaction.created_at < cutoff_date
        ).count()
        
        if old_transactions > 0:
            logger.info(f"Found {old_transactions} old budget transactions to potentially archive")
            # In a real implementation, you might archive rather than delete
        
        # Add other cleanup tasks as needed
        db.commit()


# Global background task manager instance
background_manager = BackgroundTaskManager()


# Utility functions for manual task execution
async def create_net_worth_snapshot_for_user(user_id: int):
    """Manually create a net worth snapshot for a specific user."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Calculate net worth
        total_assets = db.query(func.sum(NetWorthAsset.current_value)).filter(
            and_(NetWorthAsset.user_id == user_id, NetWorthAsset.is_active == True)
        ).scalar() or 0.0
        
        total_liabilities = db.query(func.sum(NetWorthLiability.current_balance)).filter(
            and_(NetWorthLiability.user_id == user_id, NetWorthLiability.is_active == True)
        ).scalar() or 0.0
        
        net_worth = total_assets - total_liabilities
        
        logger.info(f"Manual net worth snapshot for user {user_id}: ${net_worth:,.2f}")
        
        return {
            "user_id": user_id,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "net_worth": net_worth,
            "snapshot_date": datetime.now()
        }
        
    finally:
        db.close()


async def refresh_budget_spending(budget_id: int = None):
    """Manually refresh budget spending calculations."""
    db = SessionLocal()
    try:
        if budget_id:
            budgets = db.query(Budget).filter(Budget.id == budget_id).all()
        else:
            budgets = db.query(Budget).filter(Budget.is_active == True).all()
        
        for budget in budgets:
            current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            total_spent = db.query(func.sum(BudgetTransaction.amount)).filter(
                and_(
                    BudgetTransaction.budget_id == budget.id,
                    BudgetTransaction.transaction_date >= current_month
                )
            ).scalar() or 0.0
            
            budget.current_spent = total_spent
            logger.info(f"Refreshed budget {budget.id} spending: ${total_spent:.2f}")
        
        db.commit()
        return {"message": f"Refreshed spending for {len(budgets)} budgets"}
        
    finally:
        db.close()