"""
AWS Storage Service for Market Pulse Events
Stores pulse events to S3 and optionally DynamoDB

Environment Variables Required:
- AWS_ACCESS_KEY_ID: AWS access key
- AWS_SECRET_ACCESS_KEY: AWS secret key
- AWS_REGION: AWS region (default: us-east-1)
- AWS_S3_PULSE_BUCKET: S3 bucket name for pulse events
- AWS_DYNAMODB_PULSE_TABLE: DynamoDB table name (optional)
check
Or use IAM role if running on EC2/Lambda
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from decimal import Decimal

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
    """Service for storing Market Pulse events to AWS"""
    
    def __init__(
        self,
        s3_bucket: str = None,
        dynamodb_table: str = None,
        aws_region: str = None
    ):
        self.s3_bucket = s3_bucket or os.getenv("AWS_S3_PULSE_BUCKET")
        self.dynamodb_table = dynamodb_table or os.getenv("AWS_DYNAMODB_PULSE_TABLE")
        self.aws_region = aws_region or os.getenv("AWS_REGION", "us-east-1")
        
        # Initialize AWS clients
        self.s3_client = None
        self.dynamodb_client = None
        self.table = None
        
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
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code == '404':
                    logger.warning(f"S3 bucket '{self.s3_bucket}' does not exist")
                else:
                    logger.warning(f"Failed to initialize S3 client: {e}")
            except Exception as e:
                logger.warning(f"Failed to initialize S3 client: {e}")
        
        # Initialize DynamoDB client
        if self.dynamodb_table:
            try:
                self.dynamodb_client = boto3.resource('dynamodb', region_name=self.aws_region)
                self.table = self.dynamodb_client.Table(self.dynamodb_table)
                # Test connection
                self.table.meta.client.describe_table(TableName=self.dynamodb_table)
                logger.info(f"AWS DynamoDB client initialized for table: {self.dynamodb_table}")
            except NoCredentialsError:
                logger.warning("AWS credentials not configured - DynamoDB storage disabled")
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code == 'ResourceNotFoundException':
                    logger.warning(f"DynamoDB table '{self.dynamodb_table}' does not exist")
                else:
                    logger.warning(f"Failed to initialize DynamoDB client: {e}")
            except Exception as e:
                logger.warning(f"Failed to initialize DynamoDB client: {e}")
    
    def _convert_to_dynamodb_item(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert event dict to DynamoDB-compatible format"""
        item = {
            'timestamp': event['timestamp'],
            'ticker': event.get('ticker', 'MARKET'),
            'stress': Decimal(str(event.get('stress', 0))),
            'regime': event.get('regime', 'calm'),
            'velocity': Decimal(str(event.get('velocity', 0))),
            'data': json.dumps(event, default=str)
        }
        return item
    
    def store_pulse_event(self, event: Dict[str, Any]) -> bool:
        """
        Store a single pulse event to S3 and/or DynamoDB
        Returns True if at least one storage succeeded
        """
        s3_success = False
        dynamodb_success = False
        
        # Store to S3 (daily files)
        if self.s3_client and self.s3_bucket:
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
                s3_success = True
            except ClientError as e:
                logger.error(f"Failed to store to S3: {e}")
            except Exception as e:
                logger.error(f"Unexpected error storing to S3: {e}")
        
        # Store to DynamoDB
        if self.table and self.dynamodb_table:
            try:
                item = self._convert_to_dynamodb_item(event)
                self.table.put_item(Item=item)
                logger.debug(f"Stored pulse event to DynamoDB: {event['timestamp']}")
                dynamodb_success = True
            except ClientError as e:
                logger.error(f"Failed to store to DynamoDB: {e}")
            except Exception as e:
                logger.error(f"Unexpected error storing to DynamoDB: {e}")
        
        return s3_success or dynamodb_success
    
    def store_pulse_events_batch(self, events: List[Dict[str, Any]]) -> int:
        """
        Store multiple pulse events in batch
        Returns number of successfully stored events
        """
        success_count = 0
        
        # Batch write to DynamoDB if available
        if self.table and self.dynamodb_table and len(events) > 0:
            try:
                with self.table.batch_writer() as batch:
                    for event in events:
                        try:
                            item = self._convert_to_dynamodb_item(event)
                            batch.put_item(Item=item)
                            success_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to add event to batch: {e}")
                            continue
                logger.info(f"Batch stored {success_count} events to DynamoDB")
            except Exception as e:
                logger.error(f"Batch write to DynamoDB failed: {e}")
                success_count = 0
        
        # Also store to S3 (one by one)
        s3_count = 0
        if self.s3_client and self.s3_bucket:
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
                    s3_count += 1
                except Exception as e:
                    logger.warning(f"Failed to store event to S3: {e}")
        
        return max(success_count, s3_count)
    
    def get_pulse_events(
        self,
        start_date: datetime,
        end_date: datetime,
        ticker: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve pulse events from S3 and/or DynamoDB for a date range
        Prefers DynamoDB if available (faster queries)
        """
        events = []
        
        # Try DynamoDB first (faster for queries)
        if self.table and self.dynamodb_table:
            try:
                events = self._get_events_from_dynamodb(start_date, end_date, ticker)
                if events:
                    logger.debug(f"Retrieved {len(events)} events from DynamoDB")
                    return events
            except Exception as e:
                logger.warning(f"DynamoDB query failed, falling back to S3: {e}")
        
        # Fallback to S3
        if self.s3_client and self.s3_bucket:
            try:
                events = self._get_events_from_s3(start_date, end_date, ticker)
                logger.debug(f"Retrieved {len(events)} events from S3")
            except Exception as e:
                logger.error(f"Failed to retrieve pulse events from S3: {e}")
        
        return events
    
    def _get_events_from_dynamodb(
        self,
        start_date: datetime,
        end_date: datetime,
        ticker: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve events from DynamoDB"""
        events = []
        
        try:
            # Scan table (if timestamp is not partition key)
            # For better performance, consider using GSI with timestamp as sort key
            # Using table resource returns items directly
            scan_kwargs = {}
            if ticker:
                from boto3.dynamodb.conditions import Attr
                scan_kwargs['FilterExpression'] = Attr('ticker').eq(ticker)
            
            response = self.table.scan(**scan_kwargs)
            
            # Process initial batch
            for item in response.get('Items', []):
                event_timestamp = item.get('timestamp', '')
                try:
                    if isinstance(event_timestamp, str):
                        event_dt = datetime.fromisoformat(event_timestamp.replace('Z', '+00:00'))
                    else:
                        event_dt = event_timestamp
                    
                    if start_date <= event_dt <= end_date:
                        if ticker is None or item.get('ticker') == ticker:
                            # Parse the full event data
                            event_data = json.loads(item.get('data', '{}'))
                            events.append(event_data)
                except Exception as e:
                    logger.warning(f"Failed to parse event timestamp: {e}")
                    continue
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = self.table.scan(**scan_kwargs)
                for item in response.get('Items', []):
                    event_timestamp = item.get('timestamp', '')
                    try:
                        if isinstance(event_timestamp, str):
                            event_dt = datetime.fromisoformat(event_timestamp.replace('Z', '+00:00'))
                        else:
                            event_dt = event_timestamp
                        
                        if start_date <= event_dt <= end_date:
                            if ticker is None or item.get('ticker') == ticker:
                                event_data = json.loads(item.get('data', '{}'))
                                events.append(event_data)
                    except Exception as e:
                        continue
            
        except Exception as e:
            logger.error(f"Error querying DynamoDB: {e}")
        
        # Sort by timestamp
        events.sort(key=lambda x: x.get('timestamp', ''))
        return events
    
    def _get_events_from_s3(
        self,
        start_date: datetime,
        end_date: datetime,
        ticker: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve events from S3"""
        events = []
        
        try:
            # List objects in date range
            current_date = start_date.date()
            end_date_obj = end_date.date()
            
            while current_date <= end_date_obj:
                prefix = f"pulse-events/{current_date.isoformat()}/"
                
                paginator = self.s3_client.get_paginator('list_objects_v2')
                pages = paginator.paginate(Bucket=self.s3_bucket, Prefix=prefix)
                
                for page in pages:
                    if 'Contents' not in page:
                        continue
                    
                    for obj in page['Contents']:
                        try:
                            # Get object
                            obj_response = self.s3_client.get_object(
                                Bucket=self.s3_bucket,
                                Key=obj['Key']
                            )
                            event = json.loads(obj_response['Body'].read().decode('utf-8'))
                            
                            # Filter by ticker if specified
                            if ticker is None or event.get('ticker') == ticker:
                                events.append(event)
                        except Exception as e:
                            logger.warning(f"Failed to read S3 object {obj['Key']}: {e}")
                            continue
                
                current_date += timedelta(days=1)
            
            # Sort by timestamp
            events.sort(key=lambda x: x.get('timestamp', ''))
            
        except ClientError as e:
            logger.error(f"Failed to retrieve pulse events from S3: {e}")
        
        return events
    
    def get_daily_summaries(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get daily summaries from S3 (stored by agent)
        Returns list of summary objects
        """
        summaries = []
        
        if not self.s3_client or not self.s3_bucket:
            return summaries
        
        try:
            prefix = "daily-summaries/"
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.s3_bucket, Prefix=prefix)
            
            for page in pages:
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    try:
                        obj_response = self.s3_client.get_object(
                            Bucket=self.s3_bucket,
                            Key=obj['Key']
                        )
                        summary = json.loads(obj_response['Body'].read().decode('utf-8'))
                        summaries.append(summary)
                    except Exception as e:
                        logger.warning(f"Failed to read summary {obj['Key']}: {e}")
                        continue
            
            # Sort by date (newest first)
            summaries.sort(key=lambda x: x.get('date', ''), reverse=True)
            summaries = summaries[:days]  # Limit to requested days
            
        except Exception as e:
            logger.error(f"Failed to retrieve daily summaries: {e}")
        
        return summaries
    
    def store_daily_summary(self, summary: Dict[str, Any]) -> bool:
        """
        Store a daily summary (called by agent)
        """
        if not self.s3_client or not self.s3_bucket:
            return False
        
        try:
            date_str = summary.get('date', datetime.now().strftime("%Y-%m-%d"))
            key = f"daily-summaries/{date_str}.json"
            
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=key,
                Body=json.dumps(summary, default=str, ensure_ascii=False),
                ContentType='application/json'
            )
            logger.info(f"Stored daily summary to S3: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to store daily summary: {e}")
            return False

