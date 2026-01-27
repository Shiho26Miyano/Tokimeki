"""
AWS Storage Service for Market Pulse Events (v3 - Minimal)

Layer 2: Storage Layer (S3-only)
职责: 原始数据和处理结果的存储和检索
技术: AWS S3, boto3

数据结构:
- raw-data/v1/date=YYYY-MM-DD/ticker=SPY/bar_5m_HH-MM.jsonl.gz (Layer 1 写入)
- processed-data/v1/date=YYYY-MM-DD/pulse-events.jsonl.gz (Layer 3 写入)

Deleted (v3):
- ❌ DynamoDB support (S3-only)
- ❌ daily-summaries/ (not needed)

Environment Variables Required:
- AWS_ACCESS_KEY_ID: AWS access key
- AWS_SECRET_ACCESS_KEY: AWS secret key
- AWS_REGION: AWS region (default: us-east-2)
- AWS_S3_PULSE_BUCKET: S3 bucket name
Or use IAM role if running on EC2/Lambda
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Any, List

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    AWS_AVAILABLE = True
except ImportError:
    boto3 = None
    ClientError = None
    NoCredentialsError = None
    AWS_AVAILABLE = False

logger = logging.getLogger(__name__)


class AWSStorageService:
    """Service for storing Market Pulse events to AWS S3 (v3 - S3-only)"""
    
    def __init__(
        self,
        s3_bucket: str = None,
        aws_region: str = None
    ):
        self.s3_bucket = s3_bucket or os.getenv("AWS_S3_PULSE_BUCKET")
        self.aws_region = aws_region or os.getenv("AWS_REGION", "us-east-2")
        
        # Initialize S3 client only
        self.s3_client = None
        
        if not AWS_AVAILABLE:
            logger.warning("boto3 not available - AWS storage will be disabled")
            return
        
        # Check AWS credentials
        try:
            # Try to get credentials
            session = boto3.Session()
            credentials = session.get_credentials()
            if not credentials:
                logger.warning("AWS credentials not found - AWS storage will be disabled")
                return
        except Exception as e:
            logger.warning(f"Failed to check AWS credentials: {e}")
            return
        
        # Initialize S3 client
        if self.s3_bucket:
            try:
                self.s3_client = boto3.client('s3', region_name=self.aws_region)
                # Test connection
                self.s3_client.head_bucket(Bucket=self.s3_bucket)
                logger.info(f"AWS S3 client initialized for bucket: {self.s3_bucket}")
            except NoCredentialsError:
                logger.warning("AWS credentials not configured - S3 storage disabled")
                self.s3_client = None
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code == '404':
                    logger.warning(f"S3 bucket '{self.s3_bucket}' does not exist")
                    self.s3_client = None
                elif error_code == '403':
                    logger.warning(f"S3 bucket access forbidden (403) - IAM permissions issue")
                    logger.warning(f"  Bucket: {self.s3_bucket}")
                    logger.warning(f"  Fix: Run ./scripts/fix_s3_permissions.sh or see docs/features/marketpulse/FIX-S3-PERMISSIONS-MANUAL.md")
                    logger.warning(f"  Required permissions: s3:ListBucket on bucket, s3:GetObject/PutObject on objects")
                    self.s3_client = None
                else:
                    logger.warning(f"Failed to initialize S3 client: {e}")
                    self.s3_client = None
            except Exception as e:
                logger.warning(f"Failed to initialize S3 client: {e}")
                self.s3_client = None
        
    
    def store_pulse_event(self, event: Dict[str, Any]) -> bool:
        """
        Store a single pulse event to S3 (v3 - S3-only)
        Returns True if storage succeeded
        """
        if not self.s3_client or not self.s3_bucket:
            return False
        
        try:
            # Parse timestamp to get date
            timestamp = event.get('timestamp', datetime.now().isoformat())
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = timestamp
            
            date_str = dt.strftime("%Y-%m-%d")
            # Use timestamp as filename (sanitize for S3)
            timestamp_key = timestamp.replace(':', '-').replace('.', '-')
            key = f"pulse-events/{date_str}/{timestamp_key}.json"
            
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=key,
                Body=json.dumps(event, default=str, ensure_ascii=False),
                ContentType='application/json'
            )
            logger.debug(f"Stored pulse event to S3: {key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to store to S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error storing to S3: {e}")
            return False
    
    def store_pulse_events_batch(self, events: List[Dict[str, Any]]) -> int:
        """
        Store multiple pulse events to S3 (v3 - S3-only)
        Returns number of successfully stored events
        """
        if not self.s3_client or not self.s3_bucket:
            return 0
        
        success_count = 0
        for event in events:
            try:
                timestamp = event.get('timestamp', datetime.now().isoformat())
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    dt = timestamp
                
                date_str = dt.strftime("%Y-%m-%d")
                timestamp_key = timestamp.replace(':', '-').replace('.', '-')
                key = f"pulse-events/{date_str}/{timestamp_key}.json"
                
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=key,
                    Body=json.dumps(event, default=str, ensure_ascii=False),
                    ContentType='application/json'
                )
                success_count += 1
            except Exception as e:
                logger.warning(f"Failed to store event to S3: {e}")
        
        return success_count
    

