"""
Decision Reflection Trajectory Service
Computes trajectory data for decision reflection visualization
"""
import math
import logging
from typing import List, Dict, Any, Literal

logger = logging.getLogger(__name__)


def clamp(n: float, a: float, b: float) -> float:
    """Clamp value between a and b"""
    return max(a, min(b, n))


class DecisionReflectionService:
    """Service for computing decision reflection trajectories"""
    
    def __init__(self):
        """Initialize the service"""
        logger.info("DecisionReflectionService initialized")
    
    def build_trajectory(self, intensity: int, days: int = 14) -> List[Dict[str, Any]]:
        """
        Build trajectory data based on intensity and number of days
        
        Args:
            intensity: Decision impact intensity (0-100)
            days: Number of days in trajectory (default 14)
            
        Returns:
            List of day data dictionaries
        """
        base = clamp(intensity / 100, 0, 1)
        data = []
        rum = 0.35 + base * 0.45
        eff = 0.25 + base * 0.35
        focus = 0.15 + base * 0.25
        
        for i in range(days):
            t = i / (days - 1) if days > 1 else 0
            
            # Without reflection: rumination increases, focus/effort decrease
            without_rumination = clamp(
                rum + 0.12 * math.sin(6 * t) + 0.08 * (1 - t), 0, 1
            )
            without_focus = clamp(
                focus + 0.06 * math.sin(9 * t) - 0.05 * t, 0, 1
            )
            without_effort = clamp(
                eff + 0.08 * math.sin(7 * t) - 0.02, 0, 1
            )
            
            # With reflection: rumination decreases, focus/effort increase
            with_rumination = clamp(
                rum * (1 - 0.55 * t) - 0.04 * math.sin(5 * t), 0, 1
            )
            with_focus = clamp(
                focus + 0.55 * t - 0.03 * math.sin(6 * t), 0, 1
            )
            with_effort = clamp(
                eff + 0.35 * t - 0.02 * math.sin(7 * t), 0, 1
            )
            
            # Recovery index (higher is better)
            with_recovery = clamp(
                0.35 + 0.55 * t - 0.25 * with_rumination, 0, 1
            )
            without_recovery = clamp(
                0.25 + 0.25 * t - 0.35 * without_rumination, 0, 1
            )
            
            data.append({
                "day": i + 1,
                "with_focus": round(with_focus * 100),
                "with_rumination": round(with_rumination * 100),
                "with_effort": round(with_effort * 100),
                "with_recovery": round(with_recovery * 100),
                "without_focus": round(without_focus * 100),
                "without_rumination": round(without_rumination * 100),
                "without_effort": round(without_effort * 100),
                "without_recovery": round(without_recovery * 100),
            })
            
            # Slow drift for next iteration
            rum = clamp(rum - 0.01, 0, 1)
            eff = clamp(eff + 0.004, 0, 1)
            focus = clamp(focus + 0.003, 0, 1)
        
        return data
    
    def calculate_score(
        self, 
        data: List[Dict[str, Any]], 
        mode: Literal["with", "without"], 
        intensity: int
    ) -> int:
        """
        Calculate Decision Quality Score
        
        Args:
            data: Trajectory data
            mode: "with" or "without" reflection
            intensity: Decision impact intensity (0-100)
            
        Returns:
            Decision Quality Score (0-100)
        """
        if not data:
            return 0
        
        last = data[-1]
        focus = last[f"{mode}_focus"]
        effort = last[f"{mode}_effort"]
        recovery = last[f"{mode}_recovery"]
        rumination = last[f"{mode}_rumination"]
        
        # Weighted formula: higher focus/effort/recovery, lower rumination = better score
        raw = (
            0.35 * focus +
            0.3 * effort +
            0.25 * recovery -
            0.35 * rumination +
            0.15 * intensity
        )
        
        return int(clamp(raw, 0, 100))

