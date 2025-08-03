import time
import psutil
import asyncio
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class RequestData:
    timestamp: float
    endpoint: str
    model: Optional[str]
    response_time: float
    success: bool
    error: Optional[str] = None

class AsyncUsageService:
    def __init__(self):
        self.requests = deque(maxlen=10000)  # Keep last 10k requests
        self.model_usage = defaultdict(int)
        self.model_costs = defaultdict(float)
        self.start_time = time.time()
        self._lock = asyncio.Lock()
        
        # Start background monitoring
        asyncio.create_task(self._start_monitoring())
    
    async def track_request(
        self, 
        endpoint: str, 
        model: Optional[str] = None, 
        response_time: float = 0, 
        success: bool = True,
        error: Optional[str] = None
    ):
        """Track a single request asynchronously"""
        async with self._lock:
            request_data = RequestData(
                timestamp=time.time(),
                endpoint=endpoint,
                model=model,
                response_time=response_time,
                success=success,
                error=error
            )
            self.requests.append(request_data)
            
            if model:
                self.model_usage[model] += 1
                # Simple cost calculation
                cost_per_request = self._get_model_cost(model)
                self.model_costs[model] += cost_per_request
    
    def _get_model_cost(self, model: str) -> float:
        """Get cost per request for a model (simplified)"""
        cost_map = {
            'deepseek-chat': 0.0001,
            'deepseek-r1': 0.0002,
            'mistral-small': 0.00005,
            'qwen3-8b': 0.00003,
            'gemma-3n': 0.00002
        }
        return cost_map.get(model, 0.0001)
    
    async def get_hourly_stats(self) -> Dict[str, Any]:
        """Get hourly usage statistics in the format expected by the API"""
        async with self._lock:
            now = time.time()
            hour_ago = now - 3600
            
            # Filter requests from the last hour
            hourly_requests = [
                req for req in self.requests 
                if req.timestamp >= hour_ago
            ]
            
            # Calculate statistics
            requests = len(hourly_requests)
            response_times = [req.response_time for req in hourly_requests if req.response_time > 0]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Calculate total cost
            total_cost = sum(self.model_costs.values())
            
            # Format model costs for API
            model_costs = {}
            for model, cost in self.model_costs.items():
                model_costs[model] = {
                    "requests": self.model_usage.get(model, 0),
                    "cost": round(cost, 6)
                }
            
            return {
                "requests": requests,
                "avg_response_time": avg_response_time,
                "total_cost": round(total_cost, 6),
                "model_costs": model_costs
            }
    
    async def get_usage_stats(self, period: str = 'today') -> Dict[str, Any]:
        """Get usage statistics for a period asynchronously"""
        async with self._lock:
            now = time.time()
            
            # Calculate time range
            if period == 'today':
                start_time = now - (24 * 60 * 60)
            elif period == 'hour':
                start_time = now - (60 * 60)
            elif period == 'month':
                start_time = now - (30 * 24 * 60 * 60)
            else:
                start_time = now - (24 * 60 * 60)
            
            # Filter requests by time
            recent_requests = [
                req for req in self.requests 
                if req.timestamp >= start_time
            ]
            
            # Calculate statistics
            total_requests = len(recent_requests)
            successful_requests = len([req for req in recent_requests if req.success])
            failed_requests = total_requests - successful_requests
            
            # Calculate response times
            response_times = [req.response_time for req in recent_requests if req.response_time > 0]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Calculate costs
            total_cost = sum(self.model_costs.values())
            
            # Get memory usage
            memory_usage = psutil.virtual_memory().percent
            
            # Calculate uptime
            uptime_seconds = now - self.start_time
            uptime_hours = int(uptime_seconds // 3600)
            uptime_minutes = int((uptime_seconds % 3600) // 60)
            uptime_str = f"{uptime_hours}h {uptime_minutes}m"
            
            return {
                "success": True,
                "requests_today": total_requests,
                "requests_hour": len([req for req in recent_requests if req.timestamp >= now - 3600]),
                "requests_month": len([req for req in self.requests if req.timestamp >= now - (30 * 24 * 3600)]),
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "avg_response_time": round(avg_response_time, 3),
                "total_cost": round(total_cost, 6),
                "memory_usage": memory_usage,
                "uptime": uptime_str,
                "model_usage": dict(self.model_usage),
                "model_costs": dict(self.model_costs)
            }
    
    async def check_limits(self) -> Dict[str, Any]:
        """Check if usage limits are exceeded asynchronously"""
        stats = await self.get_usage_stats('hour')
        
        # Simple limit checking
        hourly_limit = 50
        daily_limit = 200
        
        return {
            "hourly_limit_exceeded": stats["requests_hour"] > hourly_limit,
            "daily_limit_exceeded": stats["requests_today"] > daily_limit,
            "current_hourly": stats["requests_hour"],
            "current_daily": stats["requests_today"],
            "hourly_limit": hourly_limit,
            "daily_limit": daily_limit
        }
    
    async def reset_stats(self):
        """Reset usage statistics asynchronously"""
        async with self._lock:
            self.requests.clear()
            self.model_usage.clear()
            self.model_costs.clear()
            self.start_time = time.time()
            logger.info("Usage statistics reset")
    
    async def _start_monitoring(self):
        """Start background monitoring task"""
        while True:
            try:
                # Log periodic stats
                stats = await self.get_usage_stats('hour')
                logger.info(f"Hourly stats: {stats['requests_hour']} requests, "
                          f"avg response time: {stats['avg_response_time']}s")
                
                # Sleep for 5 minutes
                await asyncio.sleep(300)
            except Exception as e:
                logger.error(f"Error in monitoring task: {e}")
                await asyncio.sleep(60)  # Shorter sleep on error 