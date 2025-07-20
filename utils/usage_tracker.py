import time
import json
import os
import psutil
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Any
import threading

class UsageTracker:
    def __init__(self):
        self.usage_data = {
            'requests': defaultdict(int),
            'api_calls': defaultdict(int),
            'errors': defaultdict(int),
            'response_times': defaultdict(list),
            'memory_usage': deque(maxlen=1000),
            'start_time': time.time()
        }
        self.lock = threading.Lock()
        
        # Load usage limits from environment
        self.daily_limit = int(os.environ.get('DAILY_REQUEST_LIMIT', 1000))
        self.hourly_limit = int(os.environ.get('HOURLY_REQUEST_LIMIT', 100))
        self.monthly_limit = int(os.environ.get('MONTHLY_REQUEST_LIMIT', 10000))
        
        # Cost tracking (estimated costs per API call)
        self.cost_per_request = {
            'mistral-small': 0.0001,  # $0.0001 per request
            'deepseek-r1': 0.0002,    # $0.0002 per request
            'deepseek-chat': 0.0002,  # $0.0002 per request
            'qwen3-8b': 0.00005,      # $0.00005 per request
            'gemma-3n': 0.00003,      # $0.00003 per request
            'hunyuan': 0.0001,        # $0.0001 per request
        }
        
        # Start background monitoring
        self.start_monitoring()

    def track_request(self, endpoint: str, model: str = None, response_time: float = None, 
                     success: bool = True, error: str = None):
        """Track a single request"""
        with self.lock:
            timestamp = datetime.now()
            date_key = timestamp.strftime('%Y-%m-%d')
            hour_key = timestamp.strftime('%Y-%m-%d-%H')
            
            # Track basic request metrics
            self.usage_data['requests'][date_key] += 1
            self.usage_data['requests'][hour_key] += 1
            
            # Track API calls by model
            if model:
                self.usage_data['api_calls'][model] += 1
            
            # Track response times
            if response_time:
                self.usage_data['response_times'][model or 'unknown'].append(response_time)
            
            # Track errors
            if not success:
                self.usage_data['errors'][error or 'unknown'] += 1
            
            # Track memory usage
            memory_percent = psutil.virtual_memory().percent
            self.usage_data['memory_usage'].append({
                'timestamp': timestamp.isoformat(),
                'memory_percent': memory_percent
            })

    def get_usage_stats(self, period: str = 'today') -> Dict[str, Any]:
        """Get usage statistics for a specific period"""
        with self.lock:
            now = datetime.now()
            
            if period == 'today':
                date_key = now.strftime('%Y-%m-%d')
                requests = self.usage_data['requests'].get(date_key, 0)
            elif period == 'hour':
                hour_key = now.strftime('%Y-%m-%d-%H')
                requests = self.usage_data['requests'].get(hour_key, 0)
            elif period == 'month':
                month_key = now.strftime('%Y-%m')
                requests = sum(v for k, v in self.usage_data['requests'].items() 
                             if k.startswith(month_key))
            else:
                requests = sum(self.usage_data['requests'].values())
            
            # Calculate costs
            total_cost = 0
            model_costs = {}
            for model, count in self.usage_data['api_calls'].items():
                cost = count * self.cost_per_request.get(model, 0.0001)
                model_costs[model] = {
                    'requests': count,
                    'cost': cost
                }
                total_cost += cost
            
            # Calculate average response times
            avg_response_times = {}
            for model, times in self.usage_data['response_times'].items():
                if times:
                    avg_response_times[model] = sum(times) / len(times)
            
            # Get memory usage
            current_memory = psutil.virtual_memory().percent
            avg_memory = 0
            if self.usage_data['memory_usage']:
                avg_memory = sum(item['memory_percent'] for item in self.usage_data['memory_usage']) / len(self.usage_data['memory_usage'])
            
            return {
                'period': period,
                'requests': requests,
                'total_cost': round(total_cost, 4),
                'model_costs': model_costs,
                'avg_response_times': avg_response_times,
                'errors': dict(self.usage_data['errors']),
                'current_memory_percent': current_memory,
                'avg_memory_percent': round(avg_memory, 2),
                'uptime_seconds': time.time() - self.usage_data['start_time'],
                'limits': {
                    'daily': self.daily_limit,
                    'hourly': self.hourly_limit,
                    'monthly': self.monthly_limit
                }
            }

    def check_limits(self) -> Dict[str, bool]:
        """Check if usage limits are exceeded"""
        stats = self.get_usage_stats()
        
        return {
            'daily_exceeded': stats['requests'] > self.daily_limit,
            'hourly_exceeded': self.get_usage_stats('hour')['requests'] > self.hourly_limit,
            'monthly_exceeded': self.get_usage_stats('month')['requests'] > self.monthly_limit
        }

    def get_cost_estimate(self, model: str, requests: int = 1) -> float:
        """Get cost estimate for a number of requests"""
        return requests * self.cost_per_request.get(model, 0.0001)

    def start_monitoring(self):
        """Start background monitoring thread"""
        def monitor():
            while True:
                try:
                    # Check limits and log warnings
                    limits = self.check_limits()
                    if any(limits.values()):
                        print(f"⚠️ Usage limits exceeded: {limits}")
                    
                    # Log usage every hour
                    if datetime.now().minute == 0:
                        stats = self.get_usage_stats()
                        print(f"📊 Hourly usage: {stats['requests']} requests, ${stats['total_cost']} cost")
                    
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    print(f"Monitoring error: {e}")
                    time.sleep(60)
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()

    def reset_stats(self):
        """Reset all usage statistics"""
        with self.lock:
            self.usage_data = {
                'requests': defaultdict(int),
                'api_calls': defaultdict(int),
                'errors': defaultdict(int),
                'response_times': defaultdict(list),
                'memory_usage': deque(maxlen=1000),
                'start_time': time.time()
            }

# Global usage tracker instance
usage_tracker = UsageTracker() 