"""
FutureQuant Trader Data Ingestion Service
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import yfinance as yf
import pandas as pd
from sqlalchemy.orm import Session

from app.models.trading_models import Symbol, Bar
from app.models.database import get_db

logger = logging.getLogger(__name__)

class FutureQuantDataService:
    """Service for ingesting futures market data"""
    
    def __init__(self):
        # Common futures contracts
        self.default_symbols = {
            "CL=F": {"venue": "CME", "asset_class": "Energy", "point_value": 1000, "tick_size": 0.01},
            "BZ=F": {"venue": "CME", "asset_class": "Energy", "point_value": 1000, "tick_size": 0.01},
            "ES=F": {"venue": "CME", "asset_class": "Equity", "point_value": 50, "tick_size": 0.25},
            "GC=F": {"venue": "CME", "asset_class": "Metals", "point_value": 100, "tick_size": 0.10},
            "SI=F": {"venue": "CME", "asset_class": "Metals", "point_value": 5000, "tick_size": 0.005},
            "ZC=F": {"venue": "CME", "asset_class": "Grains", "point_value": 50, "tick_size": 0.25},
            "MNQ=F": {"venue": "CME", "asset_class": "Equity", "point_value": 20, "tick_size": 0.25},
            "MES=F": {"venue": "CME", "asset_class": "Equity", "point_value": 5, "tick_size": 0.25}
        }
    
    async def ensure_symbols_exist(self, db: Session) -> Dict[str, int]:
        """Ensure all default symbols exist in database"""
        symbol_ids = {}
        
        for ticker, config in self.default_symbols.items():
            symbol = db.query(Symbol).filter(Symbol.ticker == ticker).first()
            if not symbol:
                symbol = Symbol(
                    ticker=ticker,
                    venue=config["venue"],
                    asset_class=config["asset_class"],
                    point_value=config["point_value"],
                    tick_size=config["tick_size"],
                    timezone="UTC"
                )
                db.add(symbol)
                db.commit()
                db.refresh(symbol)
                logger.info(f"Created symbol: {ticker}")
            
            symbol_ids[ticker] = symbol.id
        
        return symbol_ids
    
    async def ingest_data(
        self, 
        symbols: List[str], 
        start_date: str, 
        end_date: str, 
        interval: str = "1d"
    ) -> Dict[str, Any]:
        """Ingest historical data for specified symbols"""
        try:
            # Validate interval
            valid_intervals = ["1m", "5m", "15m", "30m", "1h", "1d"]
            if interval not in valid_intervals:
                raise ValueError(f"Invalid interval. Must be one of: {valid_intervals}")
            
            # Parse dates
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            results = {}
            
            for symbol in symbols:
                if symbol not in self.default_symbols:
                    logger.warning(f"Symbol {symbol} not in default symbols, skipping")
                    continue
                
                try:
                    # Download data from yfinance
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(start=start_date, end=end_date, interval=interval)
                    
                    if data.empty:
                        logger.warning(f"No data found for {symbol}")
                        continue
                    
                    # Store in database
                    db = next(get_db())
                    await self._store_bars(db, symbol, data, interval)
                    
                    results[symbol] = {
                        "status": "success",
                        "bars_count": len(data),
                        "start_date": data.index[0].strftime("%Y-%m-%d"),
                        "end_date": data.index[-1].strftime("%Y-%m-%d")
                    }
                    
                except Exception as e:
                    logger.error(f"Error ingesting {symbol}: {str(e)}")
                    results[symbol] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            return {
                "success": True,
                "results": results,
                "total_symbols": len(symbols),
                "interval": interval
            }
            
        except Exception as e:
            logger.error(f"Data ingestion error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _store_bars(self, db: Session, symbol: str, data: pd.DataFrame, interval: str):
        """Store bars in database"""
        try:
            # Get symbol ID
            symbol_obj = db.query(Symbol).filter(Symbol.ticker == symbol).first()
            if not symbol_obj:
                raise ValueError(f"Symbol {symbol} not found in database")
            
            # Convert data to bars
            bars = []
            for timestamp, row in data.iterrows():
                bar = Bar(
                    symbol_id=symbol_obj.id,
                    timestamp=timestamp.to_pydatetime(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']) if 'Volume' in row else 0,
                    interval=interval
                )
                bars.append(bar)
            
            # Bulk insert
            db.bulk_save_objects(bars)
            db.commit()
            
            logger.info(f"Stored {len(bars)} bars for {symbol}")
            
        except Exception as e:
            db.rollback()
            raise e
    
    async def get_latest_data(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get latest data for a symbol"""
        try:
            db = next(get_db())
            
            # Get symbol
            symbol_obj = db.query(Symbol).filter(Symbol.ticker == symbol).first()
            if not symbol_obj:
                raise ValueError(f"Symbol {symbol} not found")
            
            # Get latest bars
            bars = db.query(Bar).filter(
                Bar.symbol_id == symbol_obj.id
            ).order_by(
                Bar.timestamp.desc()
            ).limit(limit).all()
            
            # Convert to dict
            result = []
            for bar in bars:
                result.append({
                    "timestamp": bar.timestamp.isoformat(),
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                    "interval": bar.interval
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting latest data for {symbol}: {str(e)}")
            return []
    
    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information"""
        try:
            db = next(get_db())
            
            symbol_obj = db.query(Symbol).filter(Symbol.ticker == symbol).first()
            if not symbol_obj:
                return None
            
            return {
                "id": symbol_obj.id,
                "ticker": symbol_obj.ticker,
                "venue": symbol_obj.venue,
                "asset_class": symbol_obj.asset_class,
                "point_value": symbol_obj.point_value,
                "tick_size": symbol_obj.tick_size,
                "timezone": symbol_obj.timezone
            }
            
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {str(e)}")
            return None
