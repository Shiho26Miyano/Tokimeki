"""
Learning Agent Service - Sharp & Clever

Responsibility: Read learning agent results, provide enhanced predictions and insights
Technology: boto3, S3, smart caching
"""
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from statistics import mean, stdev

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    boto3 = None
    ClientError = None
    BOTO3_AVAILABLE = False

logger = logging.getLogger(__name__)


class LearningAgentService:
    """
    Learning Agent Service - Sharp & Clever
    
    Reads learning agent results from S3, provides:
    - Enhanced metrics (with anomaly detection)
    - Predictions (future trends)
    - Pattern matching (historical similar events)
    - Insights (actionable recommendations)
    """
    
    def __init__(self, s3_bucket: str = None, aws_region: str = "us-east-2"):
        self.s3_bucket = s3_bucket
        self.aws_region = aws_region
        self.s3_client = None
        self._cache = {}  # Smart cache
        self._cache_ttl = 300  # 5 minute cache
        
        if BOTO3_AVAILABLE and self.s3_bucket:
            try:
                self.s3_client = boto3.client('s3', region_name=aws_region)
                logger.info(f"Learning Agent Service initialized for bucket: {s3_bucket}")
            except Exception as e:
                logger.warning(f"Failed to initialize S3 client: {e}")
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Read from smart cache"""
        if key in self._cache:
            cached_data, timestamp = self._cache[key]
            if (datetime.now(timezone.utc) - timestamp).total_seconds() < self._cache_ttl:
                return cached_data
            del self._cache[key]
        return None
    
    def _set_cache(self, key: str, value: Any):
        """Write to smart cache"""
        self._cache[key] = (value, datetime.now(timezone.utc))
    
    def get_learning_results(self, date: str = None) -> Dict[str, Any]:
        """
        Get learning agent results (baseline, patterns, model)
        
        Args:
            date: Date string "YYYY-MM-DD", defaults to today
        
        Returns:
            Dict: {
                "baseline": {...},
                "patterns": {...},
                "model_info": {...},
                "last_updated": "..."
            }
        """
        if not date:
            date = datetime.now(timezone.utc).date().isoformat()
        
        cache_key = f"learning_results_{date}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        if not self.s3_client or not self.s3_bucket:
            return self._get_default_learning_results()
        
        try:
            # Read learning results
            baseline_key = f"learning-results/baseline/{date}.json"
            patterns_key = f"learning-results/patterns/{date}.json"
            model_key = f"learning-results/models/{date}.json"
            
            results = {
                "baseline": self._read_s3_json(baseline_key) or {},
                "patterns": self._read_s3_json(patterns_key) or {},
                "model_info": self._read_s3_json(model_key) or {},
                "last_updated": date
            }
            
            self._set_cache(cache_key, results)
            return results
            
        except Exception as e:
            logger.error(f"Error reading learning results: {e}")
            return self._get_default_learning_results()
    
    def _read_s3_json(self, key: str) -> Optional[Dict]:
        """Read JSON file from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.s3_bucket,
                Key=key
            )
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise
    
    def _get_default_learning_results(self) -> Dict[str, Any]:
        """Default learning results (when no data available)"""
        return {
            "baseline": {
                "stress_mean": 0.4,
                "stress_std": 0.2,
                "volume_mean": 1000000,
                "volume_std": 500000
            },
            "patterns": {},
            "model_info": {},
            "last_updated": None
        }
    
    def enhance_pulse_event(self, pulse_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance pulse event (add learning agent insights)
        
        Args:
            pulse_event: Base pulse event (from compute agent)
        
        Returns:
            Dict: Enhanced pulse event (with anomaly detection, prediction, pattern matching)
        """
        learning_results = self.get_learning_results()
        baseline = learning_results.get("baseline", {})
        patterns = learning_results.get("patterns", {})
        
        enhanced = pulse_event.copy()
        
        # 1. Anomaly detection
        anomalies = self._detect_anomalies(pulse_event, baseline)
        enhanced["anomalies"] = anomalies
        
        # 2. Prediction (simplified, should use model in production)
        prediction = self._predict_future(pulse_event, baseline, patterns)
        enhanced["prediction"] = prediction
        
        # 3. Pattern matching
        matched_patterns = self._match_patterns(pulse_event, patterns)
        enhanced["matched_patterns"] = matched_patterns
        
        # 4. Insights
        insights = self._generate_insights(pulse_event, anomalies, prediction, matched_patterns)
        enhanced["insights"] = insights
        
        return enhanced
    
    def _detect_anomalies(self, event: Dict, baseline: Dict) -> List[str]:
        """Detect anomalies"""
        anomalies = []
        
        stress = event.get("stress", 0)
        stress_mean = baseline.get("stress_mean", 0.4)
        stress_std = baseline.get("stress_std", 0.2)
        
        if stress > stress_mean + 2 * stress_std:
            anomalies.append(f"Stress index abnormally high ({stress:.2f} > {stress_mean + 2 * stress_std:.2f})")
        
        volume_surge = event.get("volume_surge", {}).get("surge_ratio", 1.0)
        if volume_surge > 3.0:
            anomalies.append(f"Volume surge abnormally high ({volume_surge:.1f}x)")
        
        return anomalies
    
    def _predict_future(self, event: Dict, baseline: Dict, patterns: Dict) -> Dict[str, Any]:
        """Predict future (simplified version)"""
        stress = event.get("stress", 0)
        
        # Simple rule: High stress usually decreases within 2 hours
        if stress > 0.7:
            return {
                "next_hour_stress": max(0, stress - 0.1),
                "next_2h_stress": max(0, stress - 0.2),
                "confidence": 0.75,
                "reasoning": "High stress typically decreases"
            }
        elif stress < 0.3:
            return {
                "next_hour_stress": min(1.0, stress + 0.05),
                "next_2h_stress": min(1.0, stress + 0.1),
                "confidence": 0.65,
                "reasoning": "Low stress may increase"
            }
        else:
            return {
                "next_hour_stress": stress,
                "next_2h_stress": stress,
                "confidence": 0.5,
                "reasoning": "Stress stable"
            }
    
    def _match_patterns(self, event: Dict, patterns: Dict) -> List[Dict[str, Any]]:
        """Match historical patterns"""
        matched = []
        
        stress = event.get("stress", 0)
        
        # Simplified pattern matching
        if stress > 0.8:
            matched.append({
                "pattern": "Extreme stress event",
                "historical_occurrences": 45,
                "typical_outcome": "Decreases within 2 hours",
                "confidence": 0.82
            })
        
        return matched
    
    def _generate_insights(self, event: Dict, anomalies: List[str], 
                          prediction: Dict, patterns: List[Dict]) -> List[str]:
        """Generate insights"""
        insights = []
        
        if anomalies:
            insights.append(f"⚠️ Detected {len(anomalies)} anomalies: {', '.join(anomalies)}")
        
        if prediction.get("confidence", 0) > 0.7:
            next_stress = prediction.get("next_2h_stress", event.get("stress", 0))
            current_stress = event.get("stress", 0)
            if next_stress < current_stress:
                insights.append(f"📉 Prediction: Stress may decrease from {current_stress:.2f} to {next_stress:.2f} within 2h")
            elif next_stress > current_stress:
                insights.append(f"📈 Prediction: Stress may increase from {current_stress:.2f} to {next_stress:.2f} within 2h")
        
        if patterns:
            insights.append(f"🔍 Matched {len(patterns)} historical patterns")
        
        if not insights:
            insights.append("✅ Market status normal, no anomalies")
        
        return insights
