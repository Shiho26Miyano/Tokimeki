"""
Mini Golf Strategy Core Service
Independent service that integrates with FutureExploratorium architecture
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from app.models.golf_models import GolfCourse, GolfHole, GolfStrategy, GolfSession
from app.models.database import get_db
from app.services.minigolfstrategy.clients.golfcourse_api import golf_course_client
from app.services.minigolfstrategy.strategy_service import golf_strategy_calculator, Club, Hazard, Hole, Conditions

logger = logging.getLogger(__name__)

class MiniGolfStrategyCoreService:
    """Core Mini Golf Strategy service - independent service layer"""
    
    def __init__(self):
        # Mini Golf Strategy specific configuration
        self.platform_config = {
            "name": "MiniGolfStrategy",
            "version": "1.0.0",
            "description": "AI-Powered Golf Strategy and Course Analysis Platform",
            "supported_features": [
                "course_discovery",
                "club_recommendations", 
                "strategy_planning",
                "performance_analytics",
                "social_features"
            ],
            "max_concurrent_sessions": 50,
            "max_courses_cached": 1000,
            "service_type": "independent",
            "dependencies": ["golfcourse_api"]
        }
    
    async def get_platform_overview(self) -> Dict[str, Any]:
        """Get comprehensive Mini Golf Strategy platform overview"""
        try:
            db = next(get_db())
            
            # Get platform statistics
            stats = {
                "courses_available": db.query(GolfCourse).count(),
                "active_sessions": db.query(GolfSession).filter(GolfSession.is_active == True).count(),
                "strategies_generated": db.query(GolfStrategy).count(),
                "total_holes_analyzed": db.query(GolfHole).count()
            }
            
            # Get recent activity
            recent_activity = await self._get_recent_activity(db)
            
            # Get system health
            system_health = await self._get_system_health()
            
            # Get course overview
            course_overview = await self._get_course_overview()
            
            return {
                "success": True,
                "platform": self.platform_config,
                "statistics": stats,
                "recent_activity": recent_activity,
                "system_health": system_health,
                "course_overview": course_overview,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting platform overview: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def search_courses(
        self, 
        query: str, 
        country: Optional[str] = None, 
        limit: int = 25
    ) -> Dict[str, Any]:
        """Search for golf courses using external API"""
        try:
            # Search courses via external API
            courses = await golf_course_client.search_courses(query, country, limit)
            
            if "error" in courses:
                return {"success": False, "error": courses["error"]}
            
            # Process and format course data
            processed_courses = self._process_course_data(courses.get("courses", []))
            
            return {
                "success": True,
                "courses": processed_courses,
                "query": query,
                "total_found": len(processed_courses),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error searching courses: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def generate_strategy(
        self,
        course_id: str,
        hole_data: Dict[str, Any],
        conditions: Dict[str, Any],
        player_bag: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate AI-powered golf strategy for a hole"""
        try:
            # Convert input data to strategy calculator objects
            hole = self._create_hole_object(hole_data)
            conditions_obj = self._create_conditions_object(conditions)
            clubs = self._create_clubs_list(player_bag)
            
            # Generate strategy using AI algorithms
            strategy_result = golf_strategy_calculator.find_optimal_strategy(
                hole, clubs, conditions_obj
            )
            
            # Store strategy in database
            await self._store_strategy(strategy_result, course_id, hole_data, conditions, player_bag)
            
            return {
                "success": True,
                "strategy": strategy_result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating strategy: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_default_data(self) -> Dict[str, Any]:
        """Get default data for testing and demo purposes"""
        return {
            "hole": {
                "par": 4,
                "total_yardage": 420,
                "fairway_width": 35,
                "hazards": [
                    {"start_distance": 240, "end_distance": 270, "penalty_strokes": 1.0, "hazard_type": "water"}
                ],
                "green_size": 5000
            },
            "conditions": {
                "wind_speed": -8,
                "wind_direction": 0,
                "temperature": 72,
                "humidity": 60,
                "course_firmness": 0.6
            },
            "player_bag": [
                {"name": "Driver", "carry_distance": 250, "roll_distance": 22, "accuracy_sigma": 20, "loft_angle": 10},
                {"name": "3W", "carry_distance": 235, "roll_distance": 15, "accuracy_sigma": 18, "loft_angle": 15},
                {"name": "5i", "carry_distance": 180, "roll_distance": 6, "accuracy_sigma": 12, "loft_angle": 25},
                {"name": "7i", "carry_distance": 160, "roll_distance": 4, "accuracy_sigma": 10, "loft_angle": 35},
                {"name": "9i", "carry_distance": 140, "roll_distance": 2, "accuracy_sigma": 8, "loft_angle": 45}
            ]
        }
    
    def _process_course_data(self, courses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and format course data from API"""
        processed = []
        for course in courses:
            processed_course = {
                "id": course.get("id", ""),
                "name": course.get("name", "Unknown Course"),
                "location": course.get("location", ""),
                "country": course.get("country", ""),
                "par": course.get("par", 72),
                "yardage": course.get("yardage", 0),
                "slope_rating": course.get("slope_rating", 0),
                "course_rating": course.get("course_rating", 0),
                "description": course.get("description", ""),
                "amenities": course.get("amenities", [])
            }
            processed.append(processed_course)
        return processed
    
    def _create_hole_object(self, hole_data: Dict[str, Any]) -> Hole:
        """Create Hole object from input data"""
        hazards = []
        for hazard_data in hole_data.get("hazards", []):
            hazard = Hazard(
                start_distance=hazard_data.get("start_distance", 0),
                end_distance=hazard_data.get("end_distance", 0),
                penalty_strokes=hazard_data.get("penalty_strokes", 1.0),
                hazard_type=hazard_data.get("hazard_type", "unknown")
            )
            hazards.append(hazard)
        
        return Hole(
            par=hole_data.get("par", 4),
            total_yardage=hole_data.get("total_yardage", 400),
            fairway_width=hole_data.get("fairway_width", 35),
            hazards=hazards,
            green_size=hole_data.get("green_size", 5000)
        )
    
    def _create_conditions_object(self, conditions: Dict[str, Any]) -> Conditions:
        """Create Conditions object from input data"""
        return Conditions(
            wind_speed=conditions.get("wind_speed", 0),
            wind_direction=conditions.get("wind_direction", 0),
            temperature=conditions.get("temperature", 70),
            humidity=conditions.get("humidity", 50),
            course_firmness=conditions.get("course_firmness", 0.5)
        )
    
    def _create_clubs_list(self, player_bag: List[Dict[str, Any]]) -> List[Club]:
        """Create list of Club objects from player bag data"""
        clubs = []
        for club_data in player_bag:
            club = Club(
                name=club_data.get("name", ""),
                carry_distance=club_data.get("carry_distance", 0),
                roll_distance=club_data.get("roll_distance", 0),
                accuracy_sigma=club_data.get("accuracy_sigma", 15),
                loft_angle=club_data.get("loft_angle", 0)
            )
            clubs.append(club)
        return clubs
    
    async def _store_strategy(
        self, 
        strategy_result: Dict[str, Any], 
        course_id: str,
        hole_data: Dict[str, Any],
        conditions: Dict[str, Any],
        player_bag: List[Dict[str, Any]]
    ) -> None:
        """Store strategy in database"""
        try:
            db = next(get_db())
            
            # Create strategy record
            strategy = GolfStrategy(
                course_id=course_id,
                strategy_type="tee_shot",
                recommended_club=strategy_result["recommended_strategy"]["club"],
                confidence_score=strategy_result["recommended_strategy"]["confidence_score"],
                expected_strokes=strategy_result["recommended_strategy"]["expected_strokes"],
                risk_assessment=strategy_result["recommended_strategy"]["risk_level"],
                conditions=conditions,
                player_bag=player_bag
            )
            
            db.add(strategy)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error storing strategy: {str(e)}")
    
    async def _get_recent_activity(self, db: Session) -> List[Dict[str, Any]]:
        """Get recent platform activity"""
        try:
            activities = []
            
            # Recent strategies
            recent_strategies = db.query(GolfStrategy).order_by(GolfStrategy.created_at.desc()).limit(5).all()
            for strategy in recent_strategies:
                activities.append({
                    "type": "strategy",
                    "action": f"Strategy generated for {strategy.recommended_club}",
                    "timestamp": strategy.created_at.isoformat(),
                    "confidence": strategy.confidence_score,
                    "service": "MiniGolfStrategy"
                })
            
            # Recent sessions
            recent_sessions = db.query(GolfSession).order_by(GolfSession.created_at.desc()).limit(3).all()
            for session in recent_sessions:
                activities.append({
                    "type": "session",
                    "action": f"Golf session {session.session_type}",
                    "timestamp": session.created_at.isoformat(),
                    "player": session.player_name,
                    "service": "MiniGolfStrategy"
                })
            
            # Sort by timestamp
            activities.sort(key=lambda x: x["timestamp"], reverse=True)
            return activities[:10]
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {str(e)}")
            return []
    
    async def _get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        try:
            health = {
                "status": "healthy",
                "components": {
                    "database": {"status": "healthy"},
                    "golf_course_api": {"status": "healthy"},
                    "strategy_calculator": {"status": "healthy"}
                },
                "overall_score": 1.0
            }
            
            return health
            
        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def _get_course_overview(self) -> Dict[str, Any]:
        """Get course overview statistics"""
        try:
            db = next(get_db())
            
            # Get course statistics
            total_courses = db.query(GolfCourse).count()
            courses_by_country = db.query(GolfCourse.country, db.func.count(GolfCourse.id)).group_by(GolfCourse.country).all()
            
            return {
                "total_courses": total_courses,
                "courses_by_country": dict(courses_by_country),
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting course overview: {str(e)}")
            return {"error": str(e)}
