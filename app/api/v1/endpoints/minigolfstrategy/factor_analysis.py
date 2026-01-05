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

def _generate_mock_recommendations(state: Optional[str], limit: int) -> List[Dict[str, Any]]:
    """Generate mock golf course recommendations when API is rate limited"""
    mock_courses = [
        {
            "course_id": "mock_001",
            "course_name": "Pebble Beach Golf Links",
            "club_name": "Pebble Beach Company",
            "location": {
                "city": "Pebble Beach",
                "state": state or "CA",
                "country": "United States",
                "latitude": 36.5694,
                "longitude": -121.9476
            },
            "overall_score": 9.2,
            "timing_grade": "A",
            "recommendation": "Excellent conditions with optimal weather and low crowds",
            "scores": {
                "weather": 9.5,
                "crowd_level": 8.8,
                "course_condition": 9.0,
                "overall": 9.2
            },
            "weather_data": {
                "temperature": 72,
                "conditions": "Sunny",
                "wind_speed": 8
            },
            "factors": {
                "best_time": "Early morning",
                "crowd_factor": "Low",
                "weather_factor": "Excellent"
            }
        },
        {
            "course_id": "mock_002", 
            "course_name": "Augusta National Golf Club",
            "club_name": "Augusta National Golf Club",
            "location": {
                "city": "Augusta",
                "state": state or "GA",
                "country": "United States",
                "latitude": 33.5030,
                "longitude": -82.0197
            },
            "overall_score": 8.9,
            "timing_grade": "A-",
            "recommendation": "Great conditions with moderate crowds expected",
            "scores": {
                "weather": 8.5,
                "crowd_level": 9.0,
                "course_condition": 9.2,
                "overall": 8.9
            },
            "weather_data": {
                "temperature": 75,
                "conditions": "Partly Cloudy",
                "wind_speed": 5
            },
            "factors": {
                "best_time": "Mid-morning",
                "crowd_factor": "Moderate",
                "weather_factor": "Good"
            }
        },
        {
            "course_id": "mock_003",
            "course_name": "St. Andrews Old Course",
            "club_name": "St. Andrews Links Trust",
            "location": {
                "city": "St. Andrews",
                "state": state or "Scotland",
                "country": "United Kingdom",
                "latitude": 56.3398,
                "longitude": -2.8038
            },
            "overall_score": 8.7,
            "timing_grade": "B+",
            "recommendation": "Historic course with good conditions and manageable crowds",
            "scores": {
                "weather": 7.8,
                "crowd_level": 8.5,
                "course_condition": 9.5,
                "overall": 8.7
            },
            "weather_data": {
                "temperature": 65,
                "conditions": "Overcast",
                "wind_speed": 12
            },
            "factors": {
                "best_time": "Afternoon",
                "crowd_factor": "Moderate",
                "weather_factor": "Fair"
            }
        }
    ]
    
    return mock_courses[:limit]

@router.get("/courses/all")
async def get_all_courses(
    state: Optional[str] = Query(None, description="Filter by US state"),
    limit: int = Query(100, description="Maximum number of results")
):
    """
    Get all available golf courses for dropdown selection
    """
    try:
        # Search for courses with a broad query to get many results
        search_query = "golf course"
        if state:
            search_query += f" {state}"
        
        results = await golf_course_client.search_courses(
            query=search_query,
            country="United States",
            limit=limit
        )
        
        if "error" in results:
            raise HTTPException(status_code=400, detail=results["error"])
        
        # Format results for dropdown
        courses = results.get("courses", [])
        formatted_courses = []
        
        for course in courses:
            course_name = course.get("course_name", "Unknown Course")
            club_name = course.get("club_name", "")
            city = course.get("location", {}).get("city", "")
            state_code = course.get("location", {}).get("state", "")
            
            # Create display name
            if club_name and club_name != course_name:
                display_name = f"{course_name} at {club_name}"
            else:
                display_name = course_name
            
            if city and state_code:
                display_name += f" ({city}, {state_code})"
            elif state_code:
                display_name += f" ({state_code})"
            
            formatted_courses.append({
                "id": course.get("id"),
                "name": display_name,
                "course_name": course_name,
                "club_name": club_name,
                "location": {
                    "city": city,
                    "state": state_code,
                    "country": course.get("location", {}).get("country", "US")
                }
            })
        
        return {
            "courses": formatted_courses,
            "total": len(formatted_courses),
            "state_filter": state
        }
        
    except Exception as e:
        logger.error(f"Error getting all courses: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

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
        
        # Check if this is a mock course ID
        course_data = None
        if course_id.startswith("mock_"):
            # Get mock course data from recommendations
            mock_recommendations = _generate_mock_recommendations(None, 10)
            mock_course = next((rec for rec in mock_recommendations if rec["course_id"] == course_id), None)
            
            if mock_course:
                # Convert mock recommendation format to course_data format expected by analyzer
                course_data = {
                    "id": mock_course["course_id"],
                    "name": mock_course["course_name"],
                    "club_name": mock_course["club_name"],
                    "location": mock_course["location"],
                    "par": 72,  # Default par
                    "yardage": 6800,  # Default yardage
                    "slope_rating": 130,  # Default slope rating
                    "course_rating": 72.0  # Default course rating
                }
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Mock course not found: {course_id}"
                )
        else:
            # Get course details from external API
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
        logger.error(f"Error analyzing course timing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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
        
        # Determine country based on state name
        country = "United States"  # Default
        if state in ["Scotland", "England", "Ireland"]:
            country = "United Kingdom"
        elif state == "Australia":
            country = "Australia"
        elif state == "Japan":
            country = "Japan"
        
        # Get course search results
        search_results = await golf_course_client.search_courses(
            query=search_query,
            country=country,
            limit=20  # Get more to analyze
        )
        
        if "error" in search_results:
            # If rate limited, return mock recommendations instead of failing
            if "rate limit" in search_results["error"].lower():
                logger.warning(f"Golf API rate limited, returning mock recommendations")
                return {
                    "recommendations": _generate_mock_recommendations(state, limit),
                    "message": "Using cached recommendations due to API rate limits",
                    "data_source": "mock"
                }
            else:
                raise HTTPException(status_code=400, detail=search_results["error"])
        
        courses = search_results.get("courses", [])
        if not courses:
            return {"recommendations": [], "message": "No courses found"}
        
        # Process courses in parallel with timeout handling
        import asyncio
        from concurrent.futures import as_completed
        
        async def analyze_single_course(course):
            """Analyze a single course with timeout and error handling"""
            try:
                course_id = course["id"]
                course_name = course.get("course_name", course.get("name", "Unknown"))
                
                logger.info(f"Analyzing course {course_id}: {course_name}")
                
                # Get course details with timeout
                course_data = await asyncio.wait_for(
                    golf_course_client.get_course_details(course_id),
                    timeout=15.0  # 15 second timeout for course details
                )
                
                if "error" in course_data:
                    logger.warning(f"Error in course data for {course_id}: {course_data.get('error')}")
                    return None
                
                logger.info(f"Course data retrieved for {course_id}")
                
                # Analyze course timing with timeout
                analysis = await asyncio.wait_for(
                    golf_factor_analyzer.analyze_course_timing(course_data),
                    timeout=30.0  # 30 second timeout for analysis
                )
                
                logger.info(f"Analysis completed for {course_id}, overall score: {analysis.get('scores', {}).get('overall', 'N/A')}")
                
                return {
                    "course_id": course_id,
                    "course_name": course_name,
                    "club_name": course.get("club_name"),
                    "location": course.get("location", {}),
                    "overall_score": analysis["scores"]["overall"],
                    "timing_grade": analysis["timing_grade"],
                    "recommendation": analysis["recommendation"],
                    "scores": analysis["scores"],
                    "weather_data": analysis["weather_data"],
                    "factors": analysis.get("factors", {})
                }
                
            except asyncio.TimeoutError:
                logger.warning(f"Timeout analyzing course {course.get('id', 'unknown')}")
                return None
            except Exception as e:
                logger.error(f"Error analyzing course {course.get('id', 'unknown')}: {e}", exc_info=True)
                return None
        
        # Process courses in parallel (limit to 5 concurrent to avoid overwhelming APIs)
        semaphore = asyncio.Semaphore(5)
        
        async def analyze_with_semaphore(course):
            async with semaphore:
                return await analyze_single_course(course)
        
        # Create tasks for parallel processing
        tasks = [analyze_with_semaphore(course) for course in courses[:10]]  # Limit to first 10 for analysis
        
        # Wait for all tasks to complete with overall timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=120.0  # 2 minute overall timeout
            )
        except asyncio.TimeoutError:
            logger.warning("Overall timeout reached for recommendations analysis")
            results = []
        
        # Filter out None results and exceptions
        recommendations = []
        for result in results:
            if result is not None and not isinstance(result, Exception):
                recommendations.append(result)
        
        # Sort by overall score
        recommendations.sort(key=lambda x: x["overall_score"], reverse=True)
        
        return {
            "recommendations": recommendations[:limit],
            "analysis_date": datetime.now().isoformat(),
            "state_filter": state,
            "total_analyzed": len(recommendations)
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
