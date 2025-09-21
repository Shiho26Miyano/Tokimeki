"""
Golf-specific database models and Pydantic schemas
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

Base = declarative_base()

class GolfCourse(Base):
    __tablename__ = "golf_courses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255))
    country = Column(String(100))
    par = Column(Integer)
    yardage = Column(Integer)
    slope_rating = Column(Float)
    course_rating = Column(Float)
    holes = Column(Integer, default=18)
    description = Column(Text)
    amenities = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    golf_holes = relationship("GolfHole", back_populates="course")
    strategies = relationship("GolfStrategy", back_populates="course")

class GolfHole(Base):
    __tablename__ = "golf_holes"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("golf_courses.id"))
    hole_number = Column(Integer, nullable=False)
    par = Column(Integer, nullable=False)
    yardage = Column(Integer, nullable=False)
    handicap = Column(Integer)
    description = Column(Text)
    hazards = Column(JSON)  # List of hazard information
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    course = relationship("GolfCourse", back_populates="golf_holes")

class GolfStrategy(Base):
    __tablename__ = "golf_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("golf_courses.id"))
    hole_id = Column(Integer, ForeignKey("golf_holes.id"))
    strategy_type = Column(String(100))  # "tee_shot", "approach", "putting"
    recommended_club = Column(String(50))
    confidence_score = Column(Float)
    expected_strokes = Column(Float)
    risk_assessment = Column(String(50))  # "low", "medium", "high"
    conditions = Column(JSON)  # Weather, wind, etc.
    player_bag = Column(JSON)  # Player's available clubs
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    course = relationship("GolfCourse", back_populates="strategies")

class GolfSession(Base):
    __tablename__ = "golf_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("golf_courses.id"))
    player_name = Column(String(255))
    session_type = Column(String(50))  # "practice", "round", "tournament"
    is_active = Column(Boolean, default=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    total_strokes = Column(Integer)
    score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Models for API

class CaddieAlphaRequest(BaseModel):
    """Request model for CaddieAlpha strategy calculation"""
    course_id: str
    tee_name: str
    gender: str  # "M" or "F"
    risk_budget: float = 2.5
    holes: List[int] = []  # Empty list means all holes

class HoleAnalysis(BaseModel):
    """Individual hole analysis result"""
    hole: int
    par: int
    yardage: int
    handicap: int
    volatility: float
    expected_strokes: float
    blow_up_probability: float
    caddie_score: float
    risk_cost: float
    recommended: str  # "press" or "protect"
    explanation: str

class CaddieAlphaSummary(BaseModel):
    """Summary of CaddieAlpha strategy results"""
    caddie_score_total: float
    risk_budget_used: float
    risk_budget_remaining: float
    press_holes: List[int]
    protect_holes: List[int]
    total_holes: int
    course_name: str
    tee_name: str
    gender: str

class CaddieAlphaResponse(BaseModel):
    """Complete CaddieAlpha strategy response"""
    summary: CaddieAlphaSummary
    holes: List[HoleAnalysis]

class CourseSearchRequest(BaseModel):
    """Request model for course search"""
    query: str
    country: Optional[str] = None
    limit: int = 25

class CourseDetailsRequest(BaseModel):
    """Request model for course details"""
    course_id: str
    tee_name: Optional[str] = None
    gender: Optional[str] = None
