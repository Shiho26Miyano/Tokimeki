#!/usr/bin/env python3
"""
Diagnostic script for Market Pulse data collection issues

This script helps diagnose why the Lambda compute agent is finding no raw data.
It checks:
1. S3 bucket configuration
2. Raw data availability for a specific date
3. Data collector service status
4. WebSocket connection status
"""
import os
import sys
import json
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    AWS_AVAILABLE = True
except ImportError:
    print("❌ boto3 not installed. Install with: pip install boto3")
    sys.exit(1)

def check_s3_configuration():
    """Check S3 bucket configuration"""
    print("\n" + "=" * 80)
    print("1. S3 Configuration Check")
    print("=" * 80)
    
    bucket = os.getenv("AWS_S3_PULSE_BUCKET")
    region = os.getenv("AWS_REGION", "us-east-2")
    
    if not bucket:
        print("❌ AWS_S3_PULSE_BUCKET environment variable not set")
        print("   Set it with: export AWS_S3_PULSE_BUCKET=your-bucket-name")
        return None, None
    
    print(f"✅ S3 Bucket: {bucket}")
    print(f"✅ AWS Region: {region}")
    
    # Check AWS credentials
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        if not credentials:
            print("❌ AWS credentials not configured")
            print("   Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
            return None, None
        print("✅ AWS credentials found")
    except Exception as e:
        print(f"❌ Error checking AWS credentials: {e}")
        return None, None
    
    # Test S3 connection
    try:
        s3_client = boto3.client('s3', region_name=region)
        s3_client.head_bucket(Bucket=bucket)
        print("✅ S3 bucket accessible")
        return s3_client, bucket
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == '404':
            print(f"❌ S3 bucket '{bucket}' does not exist")
        elif error_code == '403':
            print(f"❌ S3 bucket access forbidden (403)")
            print(f"   This is a permissions issue.")
            print(f"   Fix it by running: ./scripts/fix_s3_permissions.sh")
            print(f"   Or manually add S3 permissions to your IAM user/role")
        else:
            print(f"❌ Cannot access S3 bucket: {e}")
        return None, None
    except Exception as e:
        print(f"❌ Error connecting to S3: {e}")
        return None, None

def check_raw_data_for_date(s3_client, bucket: str, date: str):
    """Check if raw data exists for a specific date"""
    print("\n" + "=" * 80)
    print(f"2. Raw Data Check for {date}")
    print("=" * 80)
    
    prefix = f"raw-data/{date}/"
    
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
        
        total_files = 0
        tickers = {}
        
        for page in pages:
            if 'Contents' not in page:
                continue
            for obj in page['Contents']:
                total_files += 1
                key = obj['Key']
                # Parse: raw-data/YYYY-MM-DD/ticker/timestamp.json
                parts = key.split('/')
                if len(parts) >= 3:
                    ticker = parts[2]
                    if ticker not in tickers:
                        tickers[ticker] = 0
                    tickers[ticker] += 1
        
        if total_files == 0:
            print(f"❌ No raw data found for {date}")
            print(f"   Path: {prefix}")
            print("\n   Possible reasons:")
            print("   1. Data collector is not running")
            print("   2. Data collector failed to connect to Polygon WebSocket")
            print("   3. Data collector is not storing data to S3")
            print("   4. Date is in the future (no data collected yet)")
            return False, {}
        else:
            print(f"✅ Found {total_files} raw data files for {date}")
            print(f"   Tickers with data: {', '.join(sorted(tickers.keys()))}")
            print(f"   Files per ticker:")
            for ticker, count in sorted(tickers.items()):
                print(f"      {ticker}: {count} files")
            return True, tickers
    except Exception as e:
        print(f"❌ Error checking raw data: {e}")
        return False, {}

def check_data_collector_status():
    """Check if data collector service can be initialized"""
    print("\n" + "=" * 80)
    print("3. Data Collector Service Check")
    print("=" * 80)
    
    polygon_api_key = os.getenv("POLYGON_API_KEY")
    s3_bucket = os.getenv("AWS_S3_PULSE_BUCKET")
    
    if not polygon_api_key:
        print("❌ POLYGON_API_KEY environment variable not set")
        print("   Data collector cannot connect to Polygon WebSocket")
        print("   Set it with: export POLYGON_API_KEY=your-api-key")
        return False
    
    print("✅ POLYGON_API_KEY is set")
    
    if not s3_bucket:
        print("⚠️  AWS_S3_PULSE_BUCKET not set - data won't be stored")
        return False
    
    print("✅ AWS_S3_PULSE_BUCKET is set")
    
    # Try to initialize the service
    try:
        from app.services.marketpulse.pulse_service import MarketPulseService
        
        service = MarketPulseService(
            polygon_api_key=polygon_api_key,
            s3_bucket=s3_bucket
        )
        
        print("✅ Data collector service can be initialized")
        print(f"   Service started: {service.started}")
        print(f"   Tracked tickers: {', '.join(service.data_collector.tickers)}")
        
        # Check if WebSocket can connect (non-blocking check)
        polygon_service = service.data_collector.polygon_service
        print(f"   WebSocket service available: {polygon_service is not None}")
        
        return True
    except Exception as e:
        print(f"❌ Error initializing data collector service: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_lambda_read_path(date: str):
    """Show what path Lambda is reading from"""
    print("\n" + "=" * 80)
    print("4. Lambda Compute Agent Read Path")
    print("=" * 80)
    
    print(f"Lambda compute agent reads from:")
    print(f"  Prefix: raw-data/{date}/")
    print(f"  Pattern: raw-data/{date}/{{ticker}}/{{timestamp}}.json")
    print(f"\nExpected structure:")
    print(f"  raw-data/{date}/AAPL/2026-01-27T09-30-00-000000Z.json")
    print(f"  raw-data/{date}/AAPL/2026-01-27T09-31-00-000000Z.json")
    print(f"  raw-data/{date}/MSFT/2026-01-27T09-30-00-000000Z.json")
    print(f"  ...")

def provide_recommendations(date: str, has_raw_data: bool, collector_ok: bool):
    """Provide recommendations based on findings"""
    print("\n" + "=" * 80)
    print("5. Recommendations")
    print("=" * 80)
    
    if not has_raw_data:
        print("\n🔧 To fix the 'no raw data' issue:")
        print("\n   1. Start the data collector:")
        print("      - The data collector must be running continuously")
        print("      - It connects to Polygon WebSocket and stores data to S3")
        print("\n   2. Start the FastAPI application:")
        print("      - The app auto-starts the data collector on startup")
        print("      - Or manually start via API endpoint")
        print("\n   3. Verify data collection is working:")
        print("      python scripts/view_s3_data.py --date " + date)
        print("      python scripts/test_market_pulse_websocket.py")
        print("\n   4. For testing, create test data:")
        print("      python scripts/create_test_market_data.py")
        
        # Check if date is in the future
        try:
            target_date = datetime.fromisoformat(date).date()
            today = datetime.now(timezone.utc).date()
            if target_date > today:
                print(f"\n   ⚠️  Note: Date {date} is in the future (today is {today})")
                print("      Data collector only collects data for current/trading days")
        except:
            pass
    
    if not collector_ok:
        print("\n🔧 To fix data collector configuration:")
        print("   1. Set POLYGON_API_KEY environment variable")
        print("   2. Set AWS_S3_PULSE_BUCKET environment variable")
        print("   3. Configure AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)")
    
    # Check if S3 access failed
    # Note: s3_client and bucket are from check_s3_configuration() function
    # They may not be in scope here, so we check differently
    if not has_raw_data:
        print("\n🔧 To fix S3 access (if needed):")
        print("   1. Run the fix script: ./scripts/fix_s3_permissions.sh")
        print("   2. Or manually add S3 permissions to your IAM user:")
        print("      - s3:GetObject")
        print("      - s3:PutObject")
        print("      - s3:ListBucket")
        print("      - s3:DeleteObject (optional)")
    
    if has_raw_data and collector_ok:
        print("\n✅ Configuration looks good!")
        print("   If Lambda still shows no data, check:")
        print("   1. Lambda function has correct S3 bucket name")
        print("   2. Lambda function has S3 read permissions")
        print("   3. Date format matches (YYYY-MM-DD)")

def main():
    parser = argparse.ArgumentParser(
        description='Diagnose Market Pulse data collection issues'
    )
    parser.add_argument(
        '--date',
        type=str,
        help='Date to check (YYYY-MM-DD), default: today',
        default=None
    )
    
    args = parser.parse_args()
    
    # Determine date
    if args.date:
        date = args.date
    else:
        date = datetime.now(timezone.utc).date().isoformat()
    
    print("\n" + "=" * 80)
    print("Market Pulse Data Collection Diagnostic")
    print("=" * 80)
    print(f"Checking data for date: {date}")
    print(f"Current time: {datetime.now(timezone.utc).isoformat()}")
    
    # Step 1: Check S3 configuration
    s3_client, bucket = check_s3_configuration()
    
    # Step 2: Check raw data
    has_raw_data = False
    tickers = {}
    if s3_client and bucket:
        has_raw_data, tickers = check_raw_data_for_date(s3_client, bucket, date)
    
    # Step 3: Check data collector
    collector_ok = check_data_collector_status()
    
    # Step 4: Show Lambda read path
    check_lambda_read_path(date)
    
    # Step 5: Provide recommendations
    provide_recommendations(date, has_raw_data, collector_ok)
    
    print("\n" + "=" * 80)
    print("Diagnostic Complete")
    print("=" * 80)

if __name__ == "__main__":
    main()
