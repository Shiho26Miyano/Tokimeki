"""
Daily Pipeline Job Runner
Runnable locally and ready for cron/Lambda/EventBridge
"""
import sys
import os
import logging
from datetime import date, datetime, timedelta
from typing import List, Optional
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.models.database import get_db, SessionLocal
from app.services.simulation import (
    DailyPipelineService,
    VolatilityRegimeStrategy
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_daily_pipeline(
    symbols: List[str],
    target_date: Optional[date] = None,
    strategy_id: str = "vol_regime_v1",
    skip_ingest: bool = True
) -> dict:
    """
    Run the daily pipeline for specified symbols
    
    Args:
        symbols: List of stock symbols to process
        target_date: Date to process (defaults to yesterday if not provided)
        strategy_id: Strategy ID to use
        skip_ingest: Whether to skip data ingestion step
        
    Returns:
        Dictionary with results
    """
    if target_date is None:
        # Default to yesterday (most recent trading day)
        target_date = date.today() - timedelta(days=1)
    
    logger.info(f"Starting daily pipeline for {len(symbols)} symbols on {target_date}")
    
    # Get database session
    db: Session = next(get_db())
    
    try:
        # Initialize strategy and pipeline
        strategy = VolatilityRegimeStrategy()
        pipeline = DailyPipelineService(db, strategy)
        
        # Run pipeline for all symbols
        results = pipeline.run_pipeline_batch(
            symbols=symbols,
            target_date=target_date,
            skip_ingest=skip_ingest
        )
        
        logger.info(f"Pipeline completed: {results['summary']}")
        
        return results
        
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}", exc_info=True)
        raise
    finally:
        db.close()


def main():
    """Main entry point for daily run job"""
    parser = argparse.ArgumentParser(description="Run daily trading simulation pipeline")
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["AAPL", "SPY", "QQQ"],
        help="Stock symbols to process (default: AAPL SPY QQQ)"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Date to process (YYYY-MM-DD). Defaults to yesterday if not provided"
    )
    parser.add_argument(
        "--strategy",
        type=str,
        default="vol_regime_v1",
        help="Strategy ID (default: vol_regime_v1)"
    )
    parser.add_argument(
        "--no-skip-ingest",
        action="store_true",
        help="Do not skip data ingestion (default: skip)"
    )
    
    args = parser.parse_args()
    
    # Parse date if provided
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
            sys.exit(1)
    
    try:
        results = run_daily_pipeline(
            symbols=args.symbols,
            target_date=target_date,
            strategy_id=args.strategy,
            skip_ingest=not args.no_skip_ingest
        )
        
        # Print summary
        print("\n" + "="*60)
        print("Daily Pipeline Summary")
        print("="*60)
        print(f"Date: {results['date']}")
        print(f"Total Symbols: {results['summary']['total']}")
        print(f"Successful: {results['summary']['success']}")
        print(f"Failed: {results['summary']['failed']}")
        print("="*60)
        
        # Print per-symbol results
        for symbol, symbol_result in results['symbols'].items():
            status = "✓" if symbol_result['success'] else "✗"
            print(f"{status} {symbol}: ", end="")
            if symbol_result['success']:
                portfolio = symbol_result.get('portfolio', {})
                nav = portfolio.get('nav', 'N/A')
                pnl = portfolio.get('daily_pnl', 'N/A')
                print(f"NAV={nav:.2f}, P&L={pnl:.2f}")
            else:
                errors = symbol_result.get('errors', [])
                print(f"ERROR: {', '.join(errors)}")
        
        print("="*60)
        
        # Exit with appropriate code
        if results['summary']['failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Fatal error in daily run: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

