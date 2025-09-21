#!/usr/bin/env python3
"""
Test script for Golf Course API connectivity
"""
import asyncio
import os
import sys
import logging
from typing import Dict, Any

# Add the app directory to the path
sys.path.append('/Volumes/D/2025_Project/Tokimeki')

# Set the API key environment variable
os.environ["GOLFCOURSE_API_KEY"] = "BMUOAH535OJZPSGVGRLUJ3EJL4"

from app.services.minigolfstrategy.clients.golfcourse_api import GolfCourseAPIClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_golf_course_api():
    """Test the golf course API with the provided key"""
    print("Testing Golf Course API connectivity...")
    print(f"API Key: {os.environ.get('GOLFCOURSE_API_KEY', 'Not set')[:10]}...")
    print("-" * 50)
    
    # Initialize the client
    client = GolfCourseAPIClient()
    
    # Test 1: Search for courses
    print("\n1. Testing course search...")
    try:
        search_result = await client.search_courses(
            query="Pebble Beach",
            country="United States",
            limit=5
        )
        
        if "error" in search_result:
            print(f"❌ Search failed: {search_result['error']}")
        else:
            courses = search_result.get("courses", [])
            print(f"✅ Search successful! Found {len(courses)} courses")
            for i, course in enumerate(courses[:3], 1):
                print(f"   {i}. {course.get('course_name', 'Unknown')} - {course.get('club_name', 'Unknown')}")
    except Exception as e:
        print(f"❌ Search error: {str(e)}")
    
    # Test 2: Get course details (if we found courses)
    if "search_result" in locals() and "error" not in search_result:
        courses = search_result.get("courses", [])
        if courses:
            print(f"\n2. Testing course details for first course...")
            try:
                course_id = courses[0].get("id")
                if course_id:
                    details_result = await client.get_course_details(course_id)
                    
                    if "error" in details_result:
                        print(f"❌ Details failed: {details_result['error']}")
                    else:
                        print(f"✅ Course details retrieved successfully!")
                        print(f"   Course: {details_result.get('course_name', 'Unknown')}")
                        print(f"   Location: {details_result.get('location', {}).get('city', 'Unknown')}, {details_result.get('location', {}).get('state', 'Unknown')}")
                else:
                    print("❌ No course ID found in search results")
            except Exception as e:
                print(f"❌ Details error: {str(e)}")
    
    # Test 3: Test nearby courses (using a known location)
    print(f"\n3. Testing nearby courses...")
    try:
        # Using Pebble Beach coordinates as test
        nearby_result = await client.get_courses_by_location(
            latitude=36.5681,
            longitude=-121.9500,
            radius=25
        )
        
        if "error" in nearby_result:
            print(f"❌ Nearby search failed: {nearby_result['error']}")
        else:
            nearby_courses = nearby_result.get("courses", [])
            print(f"✅ Nearby search successful! Found {len(nearby_courses)} courses")
            for i, course in enumerate(nearby_courses[:3], 1):
                print(f"   {i}. {course.get('course_name', 'Unknown')} - {course.get('club_name', 'Unknown')}")
    except Exception as e:
        print(f"❌ Nearby search error: {str(e)}")
    
    # Test 4: Cache statistics
    print(f"\n4. Cache statistics...")
    cache_stats = client.get_cache_stats()
    print(f"   Cache size: {cache_stats['cache_size']}")
    print(f"   Cache TTL: {cache_stats['cache_ttl']} seconds")
    
    print("\n" + "=" * 50)
    print("Golf Course API test completed!")

if __name__ == "__main__":
    asyncio.run(test_golf_course_api())
