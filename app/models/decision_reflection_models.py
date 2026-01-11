"""
Pydantic models for Decision Reflection Engine
Stateless computation models - no database storage
"""
from typing import List, Literal
from pydantic import BaseModel, Field


class DayData(BaseModel):
    """Data for a single day in the trajectory"""
    day: int = Field(..., description="Day number (1-indexed)")
    with_focus: int = Field(..., description="Decision clarity with reflection (0-100)")
    with_rumination: int = Field(..., description="Error carryover with reflection (0-100)")
    with_effort: int = Field(..., description="Discipline with reflection (0-100)")
    with_recovery: int = Field(..., description="Recovery ability with reflection (0-100)")
    without_focus: int = Field(..., description="Decision clarity without reflection (0-100)")
    without_rumination: int = Field(..., description="Error carryover without reflection (0-100)")
    without_effort: int = Field(..., description="Discipline without reflection (0-100)")
    without_recovery: int = Field(..., description="Recovery ability without reflection (0-100)")


class TrajectoryResponse(BaseModel):
    """Response from trajectory endpoint"""
    intensity: int = Field(..., description="Decision impact intensity (0-100)")
    days: int = Field(..., description="Number of days in trajectory")
    mode: Literal["with", "without"] = Field(..., description="Reflection mode")
    score: int = Field(..., description="Decision Quality Score (0-100)")
    data: List[DayData] = Field(..., description="Trajectory data for each day")

