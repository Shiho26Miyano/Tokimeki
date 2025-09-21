"""
Golf Course Data Endpoints
Course search and details with tee information
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import logging

from app.models.golf_models import CourseSearchRequest, CourseDetailsRequest
from app.services.minigolfstrategy.clients.golfcourse_api import golf_course_client

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/courses/search")
async def search_courses(
    query: str = Query(..., description="Search query for golf courses"),
    country: Optional[str] = Query(None, description="Filter by country"),
    limit: int = Query(25, description="Maximum number of results")
):
    """
    Search for golf courses using GolfCourseAPI
    
    Returns a list of courses matching the search criteria with basic information.
    """
    try:
        result = await golf_course_client.search_courses(
            query=query,
            country=country,
            limit=limit
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=400,
                detail=f"Search failed: {result['error']}"
            )
        
        # Transform the response to include only essential course info
        courses = []
        for course in result.get("courses", []):
            courses.append({
                "id": course.get("id"),
                "course_name": course.get("course_name"),
                "club_name": course.get("club_name"),
                "location": {
                    "address": course.get("location", {}).get("address"),
                    "city": course.get("location", {}).get("city"),
                    "state": course.get("location", {}).get("state"),
                    "country": course.get("location", {}).get("country"),
                    "latitude": course.get("location", {}).get("latitude"),
                    "longitude": course.get("location", {}).get("longitude")
                },
                "available_tees": list(set([
                    tee.get("tee_name") 
                    for gender_tees in course.get("tees", {}).values() 
                    for tee in gender_tees
                ]))
            })
        
        logger.info(f"Course search completed: {len(courses)} courses found for query '{query}'")
        
        return {
            "courses": courses,
            "total_found": len(courses),
            "query": query,
            "country_filter": country
        }
        
    except Exception as e:
        logger.error(f"Error searching courses: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/courses/{course_id}")
async def get_course_details(
    course_id: str,
    tee_name: Optional[str] = Query(None, description="Specific tee to focus on"),
    gender: Optional[str] = Query(None, description="Gender for tee selection (M/F)")
):
    """
    Get detailed course information including all tee sets and hole data
    
    Returns comprehensive course data including:
    - Course basic information
    - All available tee sets for male and female players
    - Hole-by-hole details for each tee set
    - Course ratings and difficulty metrics
    """
    try:
        result = await golf_course_client.get_course_details(course_id)
        
        if "error" in result:
            raise HTTPException(
                status_code=404,
                detail=f"Course not found: {result['error']}"
            )
        
        # Transform the response to include structured tee and hole information
        course_data = {
            "id": result.get("id"),
            "course_name": result.get("course_name"),
            "club_name": result.get("club_name"),
            "location": result.get("location", {}),
            "tees": {
                "male": [],
                "female": []
            },
            "summary": {
                "total_tees": 0,
                "available_tee_names": [],
                "par_total": None,
                "total_holes": 0
            }
        }
        
        # Process tee data
        tees_data = result.get("tees", {})
        all_tee_names = set()
        
        for gender in ["male", "female"]:
            if gender in tees_data:
                for tee in tees_data[gender]:
                    tee_info = {
                        "tee_name": tee.get("tee_name"),
                        "course_rating": tee.get("course_rating"),
                        "slope_rating": tee.get("slope_rating"),
                        "bogey_rating": tee.get("bogey_rating"),
                        "total_yards": tee.get("total_yards"),
                        "total_meters": tee.get("total_meters"),
                        "number_of_holes": tee.get("number_of_holes"),
                        "par_total": tee.get("par_total"),
                        "front_course_rating": tee.get("front_course_rating"),
                        "front_slope_rating": tee.get("front_slope_rating"),
                        "back_course_rating": tee.get("back_course_rating"),
                        "back_slope_rating": tee.get("back_slope_rating"),
                        "holes": []
                    }
                    
                    # Process hole data
                    for i, hole in enumerate(tee.get("holes", []), 1):
                        hole_info = {
                            "hole_number": i,
                            "par": hole.get("par"),
                            "yardage": hole.get("yardage"),
                            "handicap": hole.get("handicap")
                        }
                        tee_info["holes"].append(hole_info)
                    
                    course_data["tees"][gender].append(tee_info)
                    all_tee_names.add(tee.get("tee_name"))
        
        # Update summary
        course_data["summary"]["total_tees"] = len(all_tee_names)
        course_data["summary"]["available_tee_names"] = sorted(list(all_tee_names))
        
        if course_data["tees"]["male"]:
            course_data["summary"]["par_total"] = course_data["tees"]["male"][0].get("par_total")
            course_data["summary"]["total_holes"] = course_data["tees"]["male"][0].get("number_of_holes")
        
        # Filter by specific tee if requested
        if tee_name and gender:
            gender_key = gender.upper()
            if gender_key in ["M", "MALE"]:
                gender_key = "male"
            elif gender_key in ["F", "FEMALE"]:
                gender_key = "female"
            else:
                raise HTTPException(status_code=400, detail="Gender must be M or F")
            
            filtered_tees = [
                tee for tee in course_data["tees"][gender_key]
                if tee["tee_name"] == tee_name
            ]
            
            if not filtered_tees:
                raise HTTPException(
                    status_code=404,
                    detail=f"Tee '{tee_name}' not found for gender '{gender}'"
                )
            
            course_data["tees"][gender_key] = filtered_tees
        
        logger.info(f"Course details retrieved for course {course_id}")
        
        return course_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting course details: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/courses/health")
async def courses_health_check():
    """Health check for courses service"""
    return {
        "status": "healthy",
        "service": "Golf Course Data Service",
        "version": "1.0.0"
    }
