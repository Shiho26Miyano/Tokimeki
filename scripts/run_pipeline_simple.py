#!/usr/bin/env python3
"""
Simple script to run the simulation pipeline for a ticker
Uses direct database access to avoid import issues
"""
import sys
import os
from datetime import date, datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.simulation.pipeline_service import DailyPipelineService
from app.services.simulation.strategy_service import VolatilityRegimeStrategy
from app.models.simulation_models import PricesDaily
from sqlalchemy import and_

def check_price_data(symbol: str, target_date: date, db: Session) -> bool:
    """Check if price data exists for the symbol and date"""
    price_data = db.query(PricesDaily).filter(
        and_(
            PricesDaily.symbol == symbol.upper(),
            PricesDaily.date == target_date
        )
    ).first()
    return price_data is not None

def ingest_prices_simple(symbol: str, target_date: date, db: Session):
    """Simple price ingestion using yfinance"""
    try:
        import yfinance as yf
        print(f"   📥 Fetching price data from yfinance...")
        
        # Get enough history for features (need at least 60 days for rv60)
        start_date = target_date - timedelta(days=100)
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=start_date, end=target_date + timedelta(days=1))
        
        if data.empty:
            print(f"   ⚠ No data found for {symbol}")
            return False
        
        ingested_count = 0
        for idx, row in data.iterrows():
            price_date = idx.date() if hasattr(idx, 'date') else date.fromisoformat(str(idx).split()[0])
            
            # Skip future dates
            if price_date > target_date:
                continue
            
            # Check if already exists
            existing = db.query(PricesDaily).filter(
                and_(
                    PricesDaily.symbol == symbol.upper(),
                    PricesDaily.date == price_date
                )
            ).first()
            
            if existing:
                continue
            
            price = PricesDaily(
                symbol=symbol.upper(),
                date=price_date,
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume']),
                adjusted_close=float(row['Close']) if 'Adj Close' not in row else float(row['Adj Close']),
                split_factor=1.0
            )
            
            db.add(price)
            ingested_count += 1
        
        db.commit()
        print(f"   ✓ Ingested {ingested_count} price records")
        return True
        
    except ImportError:
        print(f"   ⚠ yfinance not installed. Install with: pip install yfinance")
        return False
    except Exception as e:
        print(f"   ⚠ Error ingesting prices: {e}")
        db.rollback()
        return False

def run_pipeline_for_ticker(symbol: str, target_date: date = None):
    """Run the simulation pipeline for a ticker"""
    if target_date is None:
        target_date = date.today() - timedelta(days=1)
    
    print(f"🚀 Generating simulation data for {symbol} on {target_date}")
    print("=" * 60)
    
    db: Session = next(get_db())
    
    try:
        # Step 1: Check and ingest price data if needed
        print(f"\n💰 Step 1: Checking price data...")
        if not check_price_data(symbol, target_date, db):
            print(f"   Price data not found. Attempting to ingest...")
            if not ingest_prices_simple(symbol, target_date, db):
                print(f"   ❌ Cannot proceed without price data")
                print(f"   💡 Install yfinance: pip install yfinance")
                print(f"   💡 Or manually add price data to prices_daily table")
                return
        else:
            print(f"   ✓ Price data exists")
        
        # Step 2: Run the pipeline
        print(f"\n⚙️  Step 2: Running simulation pipeline...")
        strategy = VolatilityRegimeStrategy()
        pipeline = DailyPipelineService(db, strategy)
        
        result = pipeline.run_pipeline(
            symbol.upper(),
            target_date,
            skip_ingest=True  # We handle ingestion separately
        )
        
        if result['success']:
            print(f"   ✓ Pipeline completed successfully!")
            print(f"\n📈 Results:")
            if 'portfolio' in result and result['portfolio']:
                portfolio = result['portfolio']
                nav = portfolio.get('nav', 'N/A')
                pnl = portfolio.get('daily_pnl', 'N/A')
                if isinstance(nav, (int, float)):
                    print(f"   NAV: ${nav:,.2f}")
                else:
                    print(f"   NAV: {nav}")
                if isinstance(pnl, (int, float)):
                    print(f"   Daily P&L: ${pnl:,.2f}")
                else:
                    print(f"   Daily P&L: {pnl}")
            
            if 'steps' in result:
                steps = result['steps']
                print(f"\n✅ Steps completed:")
                for step_name, step_result in steps.items():
                    status = "✓" if step_result.get('success', False) else "✗"
                    print(f"   {status} {step_name}")
        else:
            print(f"   ✗ Pipeline failed:")
            for error in result.get('errors', []):
                print(f"      - {error}")
        
        print("\n" + "=" * 60)
        print("✅ Done! Refresh your dashboard to see the data.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run simulation pipeline for a ticker")
    parser.add_argument(
        "--symbol",
        type=str,
        required=True,
        help="Stock symbol (e.g., COST, AAPL)"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Date in YYYY-MM-DD format (defaults to yesterday)"
    )
    
    args = parser.parse_args()
    
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"❌ Invalid date format: {args.date}. Use YYYY-MM-DD")
            sys.exit(1)
    
    run_pipeline_for_ticker(args.symbol.upper(), target_date)


if __name__ == "__main__":
    main()

