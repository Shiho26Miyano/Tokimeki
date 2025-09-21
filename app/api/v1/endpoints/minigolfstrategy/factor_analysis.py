"""
Golf Course Factor Analysis Endpoints
AI-powered timing analysis for optimal golf course selection
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from app.services.minigolfstrategy.factor_analysis_service import golf_factor_analyzer
from app.services.minigolfstrategy.clients.golfcourse_api import golf_course_client

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/courses/search")
async def search_courses(
    query: str = Query(..., description="Search term for golf courses"),
    state: Optional[str] = Query(None, description="Filter by US state"),
    limit: int = Query(25, description="Maximum number of results")
):
    """
    Search for golf courses in the United States
    """
    try:
        # Search courses with country filter for US
        search_params = {"search_query": query, "country": "United States"}
        if state:
            search_params["state"] = state
        
        results = await golf_course_client.search_courses(
            query=query,
            country="United States",
            limit=limit
        )
        
        if "error" in results:
            raise HTTPException(status_code=400, detail=results["error"])
        
        # Filter and format results
        courses = results.get("courses", [])
        formatted_courses = []
        
        for course in courses:
            formatted_courses.append({
                "id": course.get("id"),
                "name": course.get("course_name"),
                "club_name": course.get("club_name"),
                "location": {
                    "city": course.get("location", {}).get("city"),
                    "state": course.get("location", {}).get("state"),
                    "country": course.get("location", {}).get("country")
                },
                "coordinates": {
                    "latitude": course.get("location", {}).get("latitude"),
                    "longitude": course.get("location", {}).get("longitude")
                }
            })
        
        return {
            "courses": formatted_courses,
            "total": len(formatted_courses),
            "query": query,
            "state_filter": state
        }
        
    except Exception as e:
        logger.error(f"Error searching courses: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/courses/{course_id}/timing-analysis")
async def analyze_course_timing(
    course_id: str,
    target_date: Optional[str] = Query(None, description="Target date in YYYY-MM-DD format")
):
    """
    Analyze optimal timing for a specific golf course
    """
    try:
        # Parse target date
        if target_date:
            try:
                target_dt = datetime.strptime(target_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        else:
            target_dt = datetime.now()
        
        # Get course details
        course_data = await golf_course_client.get_course_details(course_id)
        
        if "error" in course_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Course not found: {course_data['error']}"
            )
        
        # Perform factor analysis
        analysis = await golf_factor_analyzer.analyze_course_timing(
            course_data, 
            target_dt
        )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing course timing: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/courses/top-recommendations")
async def get_top_recommendations(
    state: Optional[str] = Query(None, description="Filter by US state"),
    limit: int = Query(10, description="Number of top recommendations")
):
    """
    Get top golf course recommendations based on current conditions
    """
    try:
        # Search for popular courses in the state
        search_query = "golf course"
        if state:
            search_query += f" {state}"
        
        # Get course search results
        search_results = await golf_course_client.search_courses(
            query=search_query,
            country="United States",
            limit=20  # Get more to analyze
        )
        
        if "error" in search_results:
            raise HTTPException(status_code=400, detail=search_results["error"])
        
        courses = search_results.get("courses", [])
        if not courses:
            return {"recommendations": [], "message": "No courses found"}
        
        # Analyze each course
        recommendations = []
        for course in courses[:10]:  # Limit to first 10 for analysis
            try:
                logger.info(f"Analyzing course {course['id']}: {course.get('name', 'Unknown')}")
                course_data = await golf_course_client.get_course_details(course["id"])
                if "error" not in course_data:
                    logger.info(f"Course data retrieved for {course['id']}")
                    analysis = await golf_factor_analyzer.analyze_course_timing(course_data)
                    logger.info(f"Analysis completed for {course['id']}, overall score: {analysis.get('scores', {}).get('overall', 'N/A')}")
                    recommendations.append({
                        "course_id": course["id"],
                        "course_name": course.get("course_name"),
                        "club_name": course.get("club_name"),
                        "location": course.get("location", {}),
                        "overall_score": analysis["scores"]["overall"],
                        "timing_grade": analysis["timing_grade"],
                        "recommendation": analysis["recommendation"],
                        "scores": analysis["scores"],
                        "weather_data": analysis["weather_data"],
                        "factors": analysis.get("factors", {})
                    })
                else:
                    logger.warning(f"Error in course data for {course['id']}: {course_data.get('error')}")
            except Exception as e:
                logger.error(f"Error analyzing course {course['id']}: {e}", exc_info=True)
                continue
        
        # Sort by overall score
        recommendations.sort(key=lambda x: x["overall_score"], reverse=True)
        
        return {
            "recommendations": recommendations[:limit],
            "analysis_date": datetime.now().isoformat(),
            "state_filter": state
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting top recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/courses/{course_id}/forecast")
async def get_course_forecast(
    course_id: str,
    days: int = Query(5, description="Number of days to forecast")
):
    """
    Get weather forecast for a golf course
    """
    try:
        # Get course details
        course_data = await golf_course_client.get_course_details(course_id)
        
        if "error" in course_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Course not found: {course_data['error']}"
            )
        
        location = course_data.get("location", {})
        lat = location.get("latitude")
        lon = location.get("longitude")
        
        if not lat or not lon:
            raise HTTPException(status_code=400, detail="Course location data not available")
        
        # Get weather forecast
        forecast_data = await golf_factor_analyzer.weather_service.get_forecast(lat, lon, days)
        
        if not forecast_data:
            raise HTTPException(status_code=500, detail="Weather forecast not available")
        
        # Process forecast data for OpenWeatherMap API 2.5
        forecast_list = forecast_data.get("list", [])
        daily_forecasts = []
        
        for item in forecast_list:
            dt = datetime.fromtimestamp(item["dt"])
            weather_score = golf_factor_analyzer.calculate_weather_score(item)
            
            daily_forecasts.append({
                "date": dt.strftime("%Y-%m-%d"),
                "time": dt.strftime("%H:%M"),
                "temperature": round(item["main"]["temp"], 1),
                "humidity": item["main"]["humidity"],
                "wind_speed": round(item["wind"]["speed"] * 2.237, 1),  # Convert m/s to mph
                "conditions": item["weather"][0]["description"],
                "weather_score": weather_score
            })
        
        return {
            "course_name": course_data.get("course_name"),
            "location": location,
            "forecast": daily_forecasts,
            "days": days
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting course forecast: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
async def factor_analysis_health():
    """Health check for factor analysis service"""
    return {
        "status": "healthy",
        "service": "Golf Course Factor Analysis",
        "version": "1.0.0",
        "features": [
            "Weather Analysis",
            "Seasonal Timing",
            "Crowd Analysis", 
            "AI Recommendations",
            "US Course Search"
        ]
    }
