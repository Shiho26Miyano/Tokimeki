"""
Async usage tracking utilities
"""
import asyncio
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class UsageEvent:
    """Usage event data structure"""
    timestamp: float
    endpoint: str
    model: Optional[str]
    response_time: float
    success: bool
    error: Optional[str] = None
    user_id: Optional[str] = None
    ip_address: Optional[str] = None

class AsyncUsageTracker:
    """Async usage tracking utility"""
    
    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self.events = asyncio.Queue(maxsize=max_events)
        self.stats = defaultdict(int)
        self._lock = asyncio.Lock()
        
        # Start background processing
        asyncio.create_task(self._process_events())
    
    async def track_event(self, event: UsageEvent):
        """Track a usage event asynchronously"""
        try:
            await self.events.put(event)
        except asyncio.QueueFull:
            logger.warning("Usage events queue is full, dropping event")
    
    async def track_request(
        self,
        endpoint: str,
        model: Optional[str] = None,
        response_time: float = 0,
        success: bool = True,
        error: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Track a request event"""
        event = UsageEvent(
            timestamp=time.time(),
            endpoint=endpoint,
            model=model,
            response_time=response_time,
            success=success,
            error=error,
            user_id=user_id,
            ip_address=ip_address
        )
        
        await self.track_event(event)
    
    async def get_stats(self, period: str = "hour") -> Dict[str, Any]:
        """Get usage statistics for a period"""
        async with self._lock:
            now = time.time()
            
            # Calculate time range
            if period == "hour":
                start_time = now - 3600
            elif period == "day":
                start_time = now - 86400
            elif period == "week":
                start_time = now - 604800
            else:
                start_time = now - 3600  # Default to hour
            
            # Count events in time range
            total_requests = 0
            successful_requests = 0
            failed_requests = 0
            total_response_time = 0
            model_usage = defaultdict(int)
            
            # Process events (simplified - in real implementation would query stored events)
            # This is a placeholder for the actual statistics calculation
            
            return {
                "period": period,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "avg_response_time": total_response_time / total_requests if total_requests > 0 else 0,
                "model_usage": dict(model_usage),
                "timestamp": now
            }
    
    async def _process_events(self):
        """Background task to process usage events"""
        while True:
            try:
                # Wait for events
                event = await asyncio.wait_for(self.events.get(), timeout=1.0)
                
                # Process event
                async with self._lock:
                    self.stats[f"{event.endpoint}_total"] += 1
                    
                    if event.success:
                        self.stats[f"{event.endpoint}_success"] += 1
                    else:
                        self.stats[f"{event.endpoint}_failed"] += 1
                    
                    if event.model:
                        self.stats[f"model_{event.model}"] += 1
                    
                    # Update response time stats
                    self.stats[f"{event.endpoint}_response_time"] += event.response_time
                
                # Mark task as done
                self.events.task_done()
                
            except asyncio.TimeoutError:
                # No events, continue
                continue
            except Exception as e:
                logger.error(f"Error processing usage event: {e}")
                await asyncio.sleep(1)

class AsyncUsageMetrics:
    """Async usage metrics utility"""
    
    def __init__(self, tracker: AsyncUsageTracker):
        self.tracker = tracker
    
    async def get_endpoint_metrics(self, endpoint: str, period: str = "hour") -> Dict[str, Any]:
        """Get metrics for a specific endpoint"""
        stats = await self.tracker.get_stats(period)
        
        return {
            "endpoint": endpoint,
            "total_requests": stats.get(f"{endpoint}_total", 0),
            "successful_requests": stats.get(f"{endpoint}_success", 0),
            "failed_requests": stats.get(f"{endpoint}_failed", 0),
            "avg_response_time": stats.get(f"{endpoint}_response_time", 0) / max(stats.get(f"{endpoint}_total", 1), 1),
            "period": period
        }
    
    async def get_model_metrics(self, model: str, period: str = "hour") -> Dict[str, Any]:
        """Get metrics for a specific model"""
        stats = await self.tracker.get_stats(period)
        
        return {
            "model": model,
            "total_requests": stats.get(f"model_{model}", 0),
            "period": period
        } 