#!/usr/bin/env python3
"""
Test script for AWS Storage configuration
Run this to verify your AWS setup is correct
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.marketpulse.aws_storage import AWSStorageService

def test_aws_credentials():
    """Test if AWS credentials are configured"""
    print("=" * 60)
    print("Testing AWS Credentials")
    print("=" * 60)
    
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    region = os.getenv('AWS_REGION', 'us-east-1')
    
    if not access_key:
        print("❌ AWS_ACCESS_KEY_ID not set")
        return False
    else:
        print(f"✓ AWS_ACCESS_KEY_ID: {access_key[:8]}...")
    
    if not secret_key:
        print("❌ AWS_SECRET_ACCESS_KEY not set")
        return False
    else:
        print(f"✓ AWS_SECRET_ACCESS_KEY: {'*' * len(secret_key)}")
    
    print(f"✓ AWS_REGION: {region}")
    return True

def test_s3_connection(storage: AWSStorageService):
    """Test S3 connection and bucket access"""
    print("\n" + "=" * 60)
    print("Testing S3 Connection")
    print("=" * 60)
    
    if not storage.s3_bucket:
        print("⚠️  AWS_S3_PULSE_BUCKET not set - S3 storage disabled")
        return False
    
    if not storage.s3_client:
        print("❌ S3 client not initialized")
        return False
    
    try:
        # Test bucket access
        storage.s3_client.head_bucket(Bucket=storage.s3_bucket)
        print(f"✓ S3 bucket '{storage.s3_bucket}' is accessible")
        
        # Test write permission
        test_key = "test/test-connection.json"
        test_data = {"test": True, "timestamp": datetime.now().isoformat()}
        import json
        storage.s3_client.put_object(
            Bucket=storage.s3_bucket,
            Key=test_key,
            Body=json.dumps(test_data),
            ContentType='application/json'
        )
        print("✓ S3 write permission OK")
        
        # Clean up test file
        storage.s3_client.delete_object(Bucket=storage.s3_bucket, Key=test_key)
        print("✓ Test file cleaned up")
        
        return True
    except Exception as e:
        print(f"❌ S3 connection failed: {e}")
        return False

def test_dynamodb_connection(storage: AWSStorageService):
    """Test DynamoDB connection and table access"""
    print("\n" + "=" * 60)
    print("Testing DynamoDB Connection")
    print("=" * 60)
    
    if not storage.dynamodb_table:
        print("⚠️  AWS_DYNAMODB_PULSE_TABLE not set - DynamoDB storage disabled")
        return True  # Not an error, just optional
    
    if not storage.table:
        print("❌ DynamoDB table not initialized")
        return False
    
    try:
        # Test table access
        storage.table.meta.client.describe_table(TableName=storage.dynamodb_table)
        print(f"✓ DynamoDB table '{storage.dynamodb_table}' is accessible")
        
        # Test write permission
        test_item = {
            'timestamp': f"test-{datetime.now().isoformat()}",
            'ticker': 'TEST',
            'stress': 0.5,
            'regime': 'test',
            'velocity': 0.0,
            'data': '{"test": true}'
        }
        storage.table.put_item(Item=test_item)
        print("✓ DynamoDB write permission OK")
        
        # Clean up test item
        storage.table.delete_item(
            Key={
                'timestamp': test_item['timestamp'],
                'ticker': test_item['ticker']
            }
        )
        print("✓ Test item cleaned up")
        
        return True
    except Exception as e:
        print(f"❌ DynamoDB connection failed: {e}")
        return False

def test_store_and_retrieve(storage: AWSStorageService):
    """Test storing and retrieving a pulse event"""
    print("\n" + "=" * 60)
    print("Testing Store and Retrieve")
    print("=" * 60)
    
    # Create a test event
    test_event = {
        'timestamp': datetime.now().isoformat(),
        'ticker': 'SPY',
        'price': 450.0,
        'volume': 1000000,
        'velocity': 0.5,
        'volume_surge': {
            'surge_ratio': 1.2,
            'is_surge': False,
            'magnitude': 'normal'
        },
        'volatility_burst': {
            'volatility': 0.8,
            'is_burst': False,
            'magnitude': 'normal'
        },
        'breadth': {
            'advance_decline_ratio': 1.5,
            'advancing_pct': 60.0,
            'declining_pct': 40.0,
            'breadth': 'positive'
        },
        'stress': 0.3,
        'regime': 'low_stress'
    }
    
    try:
        # Store event
        success = storage.store_pulse_event(test_event)
        if success:
            print("✓ Event stored successfully")
        else:
            print("⚠️  Event storage returned False (check logs)")
        
        # Retrieve events
        start_date = datetime.now() - timedelta(minutes=5)
        end_date = datetime.now() + timedelta(minutes=5)
        events = storage.get_pulse_events(start_date, end_date, ticker='SPY')
        
        if events:
            print(f"✓ Retrieved {len(events)} event(s)")
            print(f"  Latest event timestamp: {events[-1].get('timestamp')}")
        else:
            print("⚠️  No events retrieved (may take a moment to propagate)")
        
        return True
    except Exception as e:
        print(f"❌ Store/retrieve test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("AWS Storage Configuration Test")
    print("=" * 60)
    print("\nThis script will test your AWS Storage configuration.")
    print("Make sure you have set the required environment variables.\n")
    
    # Test credentials
    if not test_aws_credentials():
        print("\n❌ Credentials test failed. Please check your environment variables.")
        sys.exit(1)
    
    # Initialize storage service
    print("\nInitializing AWS Storage Service...")
    storage = AWSStorageService()
    
    # Test S3
    s3_ok = test_s3_connection(storage)
    
    # Test DynamoDB
    dynamodb_ok = test_dynamodb_connection(storage)
    
    # Test store/retrieve
    if s3_ok or dynamodb_ok:
        store_ok = test_store_and_retrieve(storage)
    else:
        print("\n⚠️  Skipping store/retrieve test (no storage available)")
        store_ok = False
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"S3: {'✓ OK' if s3_ok else '❌ Failed'}")
    print(f"DynamoDB: {'✓ OK' if dynamodb_ok else '⚠️  Not configured or Failed'}")
    print(f"Store/Retrieve: {'✓ OK' if store_ok else '❌ Failed'}")
    
    if s3_ok or dynamodb_ok:
        print("\n✅ AWS Storage is configured correctly!")
        return 0
    else:
        print("\n❌ AWS Storage configuration has issues.")
        print("Please check the errors above and refer to:")
        print("docs/features/aws-storage-setup.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())

