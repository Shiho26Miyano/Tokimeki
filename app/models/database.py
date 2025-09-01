"""
Database configuration and connection setup for FutureQuant Trader
"""
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# FutureQuant Trader Database URL from environment or default to SQLite for development
FUTUREQUANT_DATABASE_URL = os.getenv(
    "FUTUREQUANT_DATABASE_URL", 
    "sqlite:///./data/databases/futurequant_trader.db"
)

# Create FutureQuant Trader engine
if FUTUREQUANT_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        FUTUREQUANT_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=True
    )
else:
    engine = create_engine(
        FUTUREQUANT_DATABASE_URL,
        echo=True,
        pool_pre_ping=True
    )

# Create session factory for FutureQuant Trader
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for FutureQuant Trader models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency to get FutureQuant Trader database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_db():
    """Initialize FutureQuant Trader database tables"""
    Base.metadata.create_all(bind=engine)
