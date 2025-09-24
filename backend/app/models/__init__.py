"""
SQLAlchemy models for the FPTI application.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import enum
from datetime import datetime
from typing import Optional


class AssetType(enum.Enum):
    """Enumeration for different asset types."""
    STOCK = "stock"
    BOND = "bond"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    CRYPTO = "crypto"
    CASH = "cash"
    REAL_ESTATE = "real_estate"
    COMMODITY = "commodity"


class TransactionType(enum.Enum):
    """Enumeration for transaction types."""
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"


class User(Base):
    """User model for authentication and portfolio ownership."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    portfolios = relationship("Portfolio", back_populates="owner")


class Portfolio(Base):
    """Portfolio model representing a collection of assets."""
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="portfolios")
    holdings = relationship("Holding", back_populates="portfolio")
    transactions = relationship("Transaction", back_populates="portfolio")


class Asset(Base):
    """Asset model representing financial instruments."""
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    asset_type = Column(Enum(AssetType), nullable=False)
    currency = Column(String, default="USD")
    exchange = Column(String)
    sector = Column(String)
    industry = Column(String)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    holdings = relationship("Holding", back_populates="asset")
    transactions = relationship("Transaction", back_populates="asset")
    price_history = relationship("PriceHistory", back_populates="asset")


class Holding(Base):
    """Holdings model representing current positions in portfolios."""
    __tablename__ = "holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    quantity = Column(Float, default=0.0)
    average_cost = Column(Float, default=0.0)
    current_value = Column(Float, default=0.0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")
    asset = relationship("Asset", back_populates="holdings")


class Transaction(Base):
    """Transaction model for tracking all financial transactions."""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    quantity = Column(Float, default=0.0)
    price = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    fees = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")
    asset = relationship("Asset", back_populates="transactions")


class PriceHistory(Base):
    """Price history model for storing historical market data."""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float, nullable=False)
    volume = Column(Integer, default=0)
    adjusted_close = Column(Float)
    
    # Relationships
    asset = relationship("Asset", back_populates="price_history")


class NetWorthSnapshot(Base):
    """Net worth snapshots for tracking wealth over time."""
    __tablename__ = "net_worth_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    total_assets = Column(Float, default=0.0)
    total_liabilities = Column(Float, default=0.0)
    net_worth = Column(Float, default=0.0)
    portfolio_value = Column(Float, default=0.0)
    cash_value = Column(Float, default=0.0)
    real_estate_value = Column(Float, default=0.0)
    other_assets_value = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Budget(Base):
    """Budget model for financial planning."""
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    monthly_limit = Column(Float, nullable=False)
    current_spent = Column(Float, default=0.0)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())