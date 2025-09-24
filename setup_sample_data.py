"""
Quick setup script to add sample data and start the application
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.database import SessionLocal, init_db
from backend.app.models import User, Portfolio, Asset, Holding, Transaction, AssetType, TransactionType
from datetime import datetime, timedelta
import random

def create_sample_data():
    """Create sample data for testing"""
    init_db()
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(User).count() > 0:
            print("Sample data already exists")
            return
        
        # Create sample user
        user = User(
            username="demo_user",
            email="demo@example.com",
            full_name="Demo User"
        )
        db.add(user)
        db.flush()
        
        # Create sample portfolio
        portfolio = Portfolio(
            name="My Investment Portfolio",
            description="Main investment portfolio",
            user_id=user.id
        )
        db.add(portfolio)
        db.flush()
        
        # Create sample assets
        assets_data = [
            ("AAPL", "Apple Inc.", AssetType.STOCK),
            ("GOOGL", "Alphabet Inc.", AssetType.STOCK),
            ("MSFT", "Microsoft Corporation", AssetType.STOCK),
            ("TSLA", "Tesla Inc.", AssetType.STOCK),
            ("SPY", "SPDR S&P 500 ETF", AssetType.ETF)
        ]
        
        assets = []
        for symbol, name, asset_type in assets_data:
            asset = Asset(
                symbol=symbol,
                name=name,
                asset_type=asset_type
            )
            db.add(asset)
            assets.append(asset)
        
        db.flush()
        
        # Create sample holdings and transactions
        for i, asset in enumerate(assets):
            quantity = random.randint(10, 100)
            avg_price = random.uniform(50, 300)
            
            # Create holding
            holding = Holding(
                portfolio_id=portfolio.id,
                asset_id=asset.id,
                quantity=quantity,
                average_cost=avg_price
            )
            db.add(holding)
            
            # Create buy transaction
            transaction = Transaction(
                portfolio_id=portfolio.id,
                asset_id=asset.id,
                transaction_type=TransactionType.BUY,
                quantity=quantity,
                price=avg_price,
                transaction_date=datetime.now() - timedelta(days=random.randint(1, 365))
            )
            db.add(transaction)
        
        db.commit()
        print("Sample data created successfully!")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()