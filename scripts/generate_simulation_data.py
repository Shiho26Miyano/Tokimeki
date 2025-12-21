#!/usr/bin/env python3
"""
Quick script to generate simulation data for a ticker
This will:
1. Sync options data from consumer options dashboard
2. Ingest price data (if needed)
3. Run the pipeline to generate features, signals, and portfolio data
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
import asyncio

# Try to import ingestion service, but don't fail if it's not available
try:
    from app.services.simulation.data_ingestion_service import SimulationDataIngestionService
    HAS_INGESTION = True
except ImportError:
    HAS_INGESTION = False
    print("⚠ Warning: Data ingestion service not available (missing dependencies)")

async def generate_data_for_ticker(symbol: str, target_date: date = None):
    """Generate simulation data for a ticker"""
    if target_date is None:
        target_date = date.today() - timedelta(days=1)
    
    print(f"🚀 Generating simulation data for {symbol} on {target_date}")
    print("=" * 60)
    
    db: Session = next(get_db())
    
    try:
        # Step 1: Sync options data from consumer dashboard (optional)
        if HAS_INGESTION:
            print(f"\n📊 Step 1: Syncing options data from consumer dashboard...")
            try:
                ingestion_service = SimulationDataIngestionService(db)
                options_result = await ingestion_service.sync_consumer_options_to_simulation(symbol, target_date)
                
                if options_result.get('success'):
                    print(f"   ✓ Options data synced successfully")
                else:
                    print(f"   ⚠ Warning: Options sync had issues: {options_result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"   ⚠ Warning: Could not sync options data: {e}")
                print(f"   💡 Continuing without options data...")
        else:
            print(f"\n📊 Step 1: Skipping options sync (service not available)")
        
        # Step 2: Check if price data exists
        from app.models.simulation_models import PricesDaily
        from sqlalchemy import and_
        
        price_data = db.query(PricesDaily).filter(
            and_(
                PricesDaily.symbol == symbol.upper(),
                PricesDaily.date == target_date
            )
        ).first()
        
        if not price_data:
            print(f"\n💰 Step 2: Price data not found. Attempting to ingest...")
            if HAS_INGESTION:
                try:
                    ingestion_service = SimulationDataIngestionService(db)
                    # Try to ingest price data using yfinance
                    price_result = await ingestion_service.ingest_prices_from_yfinance(
                        symbol,
                        target_date - timedelta(days=100),  # Get some history
                        target_date
                    )
                    if price_result.get('success'):
                        print(f"   ✓ Price data ingested: {price_result.get('ingested_count', 0)} records")
                    else:
                        print(f"   ⚠ Warning: Price ingestion failed: {price_result.get('error', 'Unknown error')}")
                        print(f"   💡 You may need to manually add price data for {symbol} on {target_date}")
                except Exception as e:
                    print(f"   ⚠ Warning: Could not ingest prices: {e}")
                    print(f"   💡 You may need to manually add price data for {symbol} on {target_date}")
            else:
                print(f"   ⚠ Price ingestion service not available")
                print(f"   💡 You need to add price data manually for {symbol} on {target_date}")
                print(f"   💡 Or install required dependencies (yfinance)")
        else:
            print(f"\n💰 Step 2: Price data already exists")
        
        # Step 3: Run the pipeline
        print(f"\n⚙️  Step 3: Running simulation pipeline...")
        strategy = VolatilityRegimeStrategy()
        pipeline = DailyPipelineService(db, strategy)
        
        result = pipeline.run_pipeline(
            symbol.upper(),
            target_date,
            skip_ingest=True  # We already ingested above
        )
        
        if result['success']:
            print(f"   ✓ Pipeline completed successfully!")
            print(f"\n📈 Results:")
            if 'portfolio' in result:
                portfolio = result['portfolio']
                print(f"   NAV: ${portfolio.get('nav', 'N/A'):,.2f}" if isinstance(portfolio.get('nav'), (int, float)) else f"   NAV: {portfolio.get('nav', 'N/A')}")
                print(f"   Daily P&L: ${portfolio.get('daily_pnl', 'N/A'):,.2f}" if isinstance(portfolio.get('daily_pnl'), (int, float)) else f"   Daily P&L: {portfolio.get('daily_pnl', 'N/A')}")
            
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
    
    parser = argparse.ArgumentParser(description="Generate simulation data for a ticker")
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
    
    asyncio.run(generate_data_for_ticker(args.symbol.upper(), target_date))


if __name__ == "__main__":
    main()

