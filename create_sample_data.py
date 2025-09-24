"""
Sample data creation script for testing the FPTI application.
"""
import sys
import os

# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.append(backend_path)

from datetime import datetime, timedelta
import random

try:
    from app.database import SessionLocal, init_db
    from app.models import User, Portfolio, Asset, Holding, Transaction, AssetType, TransactionType
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

def create_sample_data():
    """Create sample data for testing the application."""
    db = SessionLocal()
    
    try:
        # Initialize database tables
        init_db()
        
        # Create sample user
        user = User(
            email="test@example.com",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
            full_name="Test User",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create sample portfolios
        portfolios = [
            Portfolio(
                name="Growth Portfolio",
                description="High-growth technology and growth stocks",
                user_id=user.id
            ),
            Portfolio(
                name="Income Portfolio",
                description="Dividend-focused stocks and bonds",
                user_id=user.id
            ),
            Portfolio(
                name="Retirement 401k",
                description="Long-term retirement savings",
                user_id=user.id
            )
        ]
        
        for portfolio in portfolios:
            db.add(portfolio)
        db.commit()
        
        # Create sample assets
        assets = [
            # Stocks
            Asset(symbol="AAPL", name="Apple Inc.", asset_type=AssetType.STOCK, 
                  sector="Technology", industry="Consumer Electronics"),
            Asset(symbol="GOOGL", name="Alphabet Inc.", asset_type=AssetType.STOCK,
                  sector="Technology", industry="Internet Content & Information"),
            Asset(symbol="MSFT", name="Microsoft Corporation", asset_type=AssetType.STOCK,
                  sector="Technology", industry="Software"),
            Asset(symbol="TSLA", name="Tesla Inc.", asset_type=AssetType.STOCK,
                  sector="Consumer Discretionary", industry="Automobiles"),
            Asset(symbol="AMZN", name="Amazon.com Inc.", asset_type=AssetType.STOCK,
                  sector="Consumer Discretionary", industry="Internet & Direct Marketing Retail"),
            Asset(symbol="NVDA", name="NVIDIA Corporation", asset_type=AssetType.STOCK,
                  sector="Technology", industry="Semiconductors"),
            Asset(symbol="META", name="Meta Platforms Inc.", asset_type=AssetType.STOCK,
                  sector="Technology", industry="Internet Content & Information"),
            Asset(symbol="NFLX", name="Netflix Inc.", asset_type=AssetType.STOCK,
                  sector="Consumer Discretionary", industry="Entertainment"),
            
            # ETFs
            Asset(symbol="SPY", name="SPDR S&P 500 ETF Trust", asset_type=AssetType.ETF,
                  sector="Diversified", industry="Index Fund"),
            Asset(symbol="QQQ", name="Invesco QQQ Trust Series 1", asset_type=AssetType.ETF,
                  sector="Technology", industry="Index Fund"),
            Asset(symbol="VTI", name="Vanguard Total Stock Market ETF", asset_type=AssetType.ETF,
                  sector="Diversified", industry="Index Fund"),
            
            # Bonds
            Asset(symbol="TLT", name="iShares 20+ Year Treasury Bond ETF", asset_type=AssetType.BOND,
                  sector="Government", industry="Treasury Bonds"),
            Asset(symbol="AGG", name="iShares Core U.S. Aggregate Bond ETF", asset_type=AssetType.BOND,
                  sector="Diversified", industry="Bond Fund"),
        ]
        
        for asset in assets:
            db.add(asset)
        db.commit()
        
        # Create sample transactions and holdings
        sample_transactions = []
        
        # Growth Portfolio transactions
        growth_portfolio = portfolios[0]
        growth_assets = [a for a in assets if a.symbol in ["AAPL", "GOOGL", "TSLA", "NVDA", "META"]]
        
        for i, asset in enumerate(growth_assets):
            # Initial purchase
            quantity = random.randint(10, 100)
            price = random.uniform(100, 300)
            transaction_date = datetime.now() - timedelta(days=random.randint(30, 365))
            
            transaction = Transaction(
                portfolio_id=growth_portfolio.id,
                asset_id=asset.id,
                transaction_type=TransactionType.BUY,
                quantity=quantity,
                price=price,
                total_amount=quantity * price,
                fees=random.uniform(0, 10),
                transaction_date=transaction_date
            )
            sample_transactions.append(transaction)
            
            # Create holding
            current_price = price * random.uniform(0.8, 1.4)  # Simulate price change
            holding = Holding(
                portfolio_id=growth_portfolio.id,
                asset_id=asset.id,
                quantity=quantity,
                average_cost=price,
                current_value=quantity * current_price
            )
            db.add(holding)
        
        # Income Portfolio transactions
        income_portfolio = portfolios[1]
        income_assets = [a for a in assets if a.symbol in ["MSFT", "AMZN", "SPY", "AGG", "TLT"]]
        
        for asset in income_assets:
            quantity = random.randint(20, 150)
            price = random.uniform(50, 200)
            transaction_date = datetime.now() - timedelta(days=random.randint(60, 300))
            
            transaction = Transaction(
                portfolio_id=income_portfolio.id,
                asset_id=asset.id,
                transaction_type=TransactionType.BUY,
                quantity=quantity,
                price=price,
                total_amount=quantity * price,
                fees=random.uniform(0, 15),
                transaction_date=transaction_date
            )
            sample_transactions.append(transaction)
            
            # Create holding
            current_price = price * random.uniform(0.9, 1.3)
            holding = Holding(
                portfolio_id=income_portfolio.id,
                asset_id=asset.id,
                quantity=quantity,
                average_cost=price,
                current_value=quantity * current_price
            )
            db.add(holding)
        
        # Retirement Portfolio transactions
        retirement_portfolio = portfolios[2]
        retirement_assets = [a for a in assets if a.symbol in ["VTI", "QQQ", "SPY", "AGG"]]
        
        for asset in retirement_assets:
            # Multiple purchases over time (dollar-cost averaging)
            total_quantity = 0
            total_cost = 0
            
            for month in range(12):  # 12 months of purchases
                quantity = random.randint(5, 25)
                price = random.uniform(80, 250)
                transaction_date = datetime.now() - timedelta(days=30 * month + random.randint(0, 29))
                
                transaction = Transaction(
                    portfolio_id=retirement_portfolio.id,
                    asset_id=asset.id,
                    transaction_type=TransactionType.BUY,
                    quantity=quantity,
                    price=price,
                    total_amount=quantity * price,
                    fees=random.uniform(0, 5),
                    transaction_date=transaction_date
                )
                sample_transactions.append(transaction)
                
                total_quantity += quantity
                total_cost += quantity * price
            
            # Create consolidated holding
            average_cost = total_cost / total_quantity if total_quantity > 0 else 0
            current_price = average_cost * random.uniform(0.95, 1.25)
            holding = Holding(
                portfolio_id=retirement_portfolio.id,
                asset_id=asset.id,
                quantity=total_quantity,
                average_cost=average_cost,
                current_value=total_quantity * current_price
            )
            db.add(holding)
        
        # Add all transactions
        for transaction in sample_transactions:
            db.add(transaction)
        
        # Add some dividend transactions
        dividend_assets = [a for a in assets if a.symbol in ["AAPL", "MSFT", "SPY"]]
        for asset in dividend_assets:
            for portfolio in portfolios:
                holding = db.query(Holding).filter(
                    Holding.portfolio_id == portfolio.id,
                    Holding.asset_id == asset.id
                ).first()
                
                if holding:
                    # Quarterly dividends
                    for quarter in range(4):
                        dividend_date = datetime.now() - timedelta(days=90 * quarter + random.randint(0, 30))
                        dividend_per_share = random.uniform(0.5, 2.0)
                        total_dividend = holding.quantity * dividend_per_share
                        
                        dividend_transaction = Transaction(
                            portfolio_id=portfolio.id,
                            asset_id=asset.id,
                            transaction_type=TransactionType.DIVIDEND,
                            quantity=0,
                            price=0,
                            total_amount=total_dividend,
                            fees=0,
                            transaction_date=dividend_date,
                            description=f"Quarterly dividend - ${dividend_per_share:.2f} per share"
                        )
                        db.add(dividend_transaction)
        
        db.commit()
        print("Sample data created successfully!")
        
        # Print summary
        print(f"Created {len(portfolios)} portfolios")
        print(f"Created {len(assets)} assets")
        print(f"Created {len(sample_transactions)} transactions")
        
        holdings_count = db.query(Holding).count()
        print(f"Created {holdings_count} holdings")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()