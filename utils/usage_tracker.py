import time
import psutil
import threading
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger(__name__)

class UsageTracker:
    def __init__(self):
        self.requests = deque(maxlen=10000)  # Keep last 10k requests
        self.model_usage = defaultdict(int)
        self.model_costs = defaultdict(float)
        self.start_time = time.time()
        self.lock = threading.Lock()
        
        # Start background monitoring
        self.start_monitoring()
    
    def track_request(self, endpoint: str, model: str = None, response_time: float = 0, success: bool = True):
        """Track a single request"""
        with self.lock:
            request_data = {
                'timestamp': time.time(),
                'endpoint': endpoint,
                'model': model,
                'response_time': response_time,
                'success': success
            }
            self.requests.append(request_data)
            
            if model:
                self.model_usage[model] += 1
                # Simple cost calculation (you can adjust based on actual costs)
                cost_per_request = self._get_model_cost(model)
                self.model_costs[model] += cost_per_request
    
    def _get_model_cost(self, model: str) -> float:
        """Get cost per request for a model (simplified)"""
        # Simplified cost model - adjust based on actual OpenRouter pricing
        cost_map = {
            'deepseek-chat': 0.0001,
            'deepseek-r1': 0.0002,
            'mistral-small': 0.00005,
            'qwen3-8b': 0.00003,
            'gemma-3n': 0.00002
        }
        return cost_map.get(model, 0.0001)  # Default cost
    
    def get_usage_stats(self, period: str = 'today') -> Dict[str, Any]:
        """Get usage statistics for a period"""
        with self.lock:
            now = time.time()
            
            # Calculate time range
            if period == 'today':
                start_time = now - (24 * 60 * 60)  # 24 hours
            elif period == 'hour':
                start_time = now - (60 * 60)  # 1 hour
            elif period == 'month':
                start_time = now - (30 * 24 * 60 * 60)  # 30 days
            else:
                start_time = now - (24 * 60 * 60)  # Default to today
            
            # Filter requests by time
            recent_requests = [
                req for req in self.requests 
                if req['timestamp'] >= start_time
            ]
            
            # Calculate statistics
            total_requests = len(recent_requests)
            successful_requests = len([req for req in recent_requests if req['success']])
            failed_requests = total_requests - successful_requests
            
            # Calculate response times
            response_times = [req['response_time'] for req in recent_requests if req['response_time'] > 0]
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
                "requests_hour": len([req for req in recent_requests if req['timestamp'] >= now - 3600]),
                "requests_month": len([req for req in self.requests if req['timestamp'] >= now - (30 * 24 * 3600)]),
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "avg_response_time": round(avg_response_time, 3),
                "total_cost": round(total_cost, 4),
                "memory_usage": round(memory_usage, 1),
                "uptime": uptime_str,
                "model_usage": dict(self.model_usage),
                "model_costs": dict(self.model_costs)
            }
    
    def check_limits(self) -> Dict[str, Any]:
        """Check if usage limits are exceeded"""
        stats = self.get_usage_stats('today')
        
        limits = {
            "daily_limit": 1000,
            "hourly_limit": 100,
            "monthly_limit": 10000,
            "daily_used": stats.get("requests_today", 0),
            "hourly_used": stats.get("requests_hour", 0),
            "monthly_used": stats.get("requests_month", 0),
            "daily_exceeded": stats.get("requests_today", 0) >= 1000,
            "hourly_exceeded": stats.get("requests_hour", 0) >= 100,
            "monthly_exceeded": stats.get("requests_month", 0) >= 10000
        }
        
        return limits
    
    def reset_stats(self):
        """Reset all usage statistics"""
        with self.lock:
            self.requests.clear()
            self.model_usage.clear()
            self.model_costs.clear()
            self.start_time = time.time()
            logger.info("Usage statistics reset")
    
    def start_monitoring(self):
        """Start background monitoring thread"""
        def monitor():
            while True:
                try:
                    # Log current stats every 5 minutes
                    stats = self.get_usage_stats()
                    logger.info(f"Current usage: {stats['requests_today']} requests today, "
                              f"${stats['total_cost']} total cost")
                    time.sleep(300)  # 5 minutes
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                    time.sleep(60)  # Wait 1 minute on error
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()

# Global usage tracker instance
usage_tracker = UsageTracker() 