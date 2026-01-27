"""
Market Pulse Pydantic Models
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional


class Indicator(BaseModel):
    """Market pulse indicator"""
    name: str = Field(..., description="Indicator name")
    value: float = Field(..., description="Indicator value")
    magnitude: str = Field(..., description="Indicator magnitude (normal/high/extreme)")
    description: str = Field(..., description="Indicator description")


class MarketPulseResponse(BaseModel):
    """Market Pulse API Response Model"""
    timestamp: str = Field(..., description="Event timestamp (ISO format)")
    stress_score: float = Field(..., ge=0.0, le=1.0, description="Market stress score (0-1)")
    regime: str = Field(..., description="Market regime (calm/low_stress/moderate_stress/high_stress/extreme_stress)")
    indicators: List[Dict[str, Any]] = Field(default_factory=list, description="List of market indicators")
    velocity: float = Field(..., description="Price velocity (% change)")
    volume_surge: Dict[str, Any] = Field(default_factory=dict, description="Volume surge data")
    volatility_burst: Dict[str, Any] = Field(default_factory=dict, description="Volatility burst data")
    breadth: Dict[str, Any] = Field(default_factory=dict, description="Market breadth data")
