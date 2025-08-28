"""
SQLAlchemy models for FutureQuant Trader
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base

class Symbol(Base):
    """Futures contract symbols"""
    __tablename__ = "futurequant_symbols"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), unique=True, index=True, nullable=False)
    venue = Column(String(10), nullable=False)  # CME, ICE, etc.
    asset_class = Column(String(20), nullable=False)  # Energy, Metals, etc.
    point_value = Column(Float, nullable=False)  # Dollar value per point
    tick_size = Column(Float, nullable=False)  # Minimum price movement
    timezone = Column(String(20), default="UTC")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    bars = relationship("Bar", back_populates="symbol")
    features = relationship("Feature", back_populates="symbol")
    forecasts = relationship("Forecast", back_populates="symbol")
    trades = relationship("Trade", back_populates="symbol")

class Bar(Base):
    """OHLCV price bars"""
    __tablename__ = "futurequant_bars"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("futurequant_symbols.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, default=0)
    interval = Column(String(10), nullable=False)  # 1m, 5m, 1h, 1d
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    symbol = relationship("Symbol", back_populates="bars")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_bars_symbol_timestamp', 'symbol_id', 'timestamp'),
    )

class Feature(Base):
    """Engineered features for ML models"""
    __tablename__ = "futurequant_features"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("futurequant_symbols.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    payload = Column(JSON, nullable=False)  # Feature values as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    symbol = relationship("Symbol", back_populates="features")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_features_symbol_timestamp', 'symbol_id', 'timestamp'),
    )

class Forecast(Base):
    """Model predictions and forecasts"""
    __tablename__ = "futurequant_forecasts"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("futurequant_symbols.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    horizon_minutes = Column(Integer, nullable=False)  # Forecast horizon
    q10 = Column(Float, nullable=False)  # 10th percentile
    q50 = Column(Float, nullable=False)  # 50th percentile (median)
    q90 = Column(Float, nullable=False)  # 90th percentile
    prob_up = Column(Float, nullable=False)  # Probability of price increase
    volatility = Column(Float, nullable=False)  # Predicted volatility
    model_id = Column(Integer, ForeignKey("futurequant_models.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    symbol = relationship("Symbol", back_populates="forecasts")
    model = relationship("Model", back_populates="forecasts")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_forecasts_symbol_timestamp', 'symbol_id', 'timestamp'),
    )

class Strategy(Base):
    """Trading strategies"""
    __tablename__ = "futurequant_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    params = Column(JSON, nullable=False)  # Strategy parameters
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    backtests = relationship("Backtest", back_populates="strategy")

class Backtest(Base):
    """Backtest runs"""
    __tablename__ = "futurequant_backtests"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("futurequant_strategies.id"), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    symbols = Column(JSON, nullable=False)  # List of symbol IDs
    config = Column(JSON, nullable=False)  # Backtest configuration
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    metrics = Column(JSON)  # Performance metrics
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    strategy = relationship("Strategy", back_populates="backtests")
    trades = relationship("Trade", back_populates="backtest")

class Trade(Base):
    """Individual trades"""
    __tablename__ = "futurequant_trades"
    
    id = Column(Integer, primary_key=True, index=True)
    backtest_id = Column(Integer, ForeignKey("futurequant_backtests.id"), nullable=True)
    symbol_id = Column(Integer, ForeignKey("futurequant_symbols.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # long, short
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    pnl = Column(Float, nullable=True)
    meta = Column(JSON)  # Additional trade metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    backtest = relationship("Backtest", back_populates="trades")
    symbol = relationship("Symbol", back_populates="trades")

class Model(Base):
    """ML models"""
    __tablename__ = "futurequant_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    artifact_uri = Column(String(500), nullable=False)  # Model artifact location
    params = Column(JSON, nullable=False)  # Model hyperparameters
    metrics = Column(JSON)  # Training metrics
    status = Column(String(20), default="training")  # training, active, archived
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    forecasts = relationship("Forecast", back_populates="model")

class Job(Base):
    """Background jobs"""
    __tablename__ = "futurequant_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String(50), nullable=False)  # ingest, features, train, backtest
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    logs_uri = Column(String(500))  # Log file location
    meta = Column(JSON)  # Job metadata
    error_message = Column(Text)

class User(Base):
    """System users"""
    __tablename__ = "futurequant_users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    role = Column(String(20), default="user")  # user, admin
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
