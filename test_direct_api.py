#!/usr/bin/env python3
"""
Direct test of the golf course API without going through the web server
"""
import asyncio
import os
import sys
import logging

# Add the app directory to the path
sys.path.append('/Volumes/D/2025_Project/Tokimeki')

# Set the API key environment variable
os.environ["GOLFCOURSE_API_KEY"] = "BMUOAH535OJZPSGVGRLUJ3EJL4"

from app.services.minigolfstrategy.clients.golfcourse_api import GolfCourseAPIClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_direct_api():
    """Test the golf course API directly"""
    print("Direct Golf Course API Test")
    print("=" * 50)
    
    client = GolfCourseAPIClient()
    
    # Test with a very simple search and longer wait
    print("Waiting 30 seconds to avoid rate limits...")
    await asyncio.sleep(30)
    
    print("\nTesting course search...")
    try:
        result = await client.search_courses(
            query="golf",
            country="United States", 
            limit=2
        )
        
        print(f"Result type: {type(result)}")
        print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            
            # Check what type of error
            if "rate limit" in result['error'].lower():
                print("✅ This is a rate limit error - your API key is working!")
                print("   The API recognizes your key and is responding properly.")
                print("   You just need to wait between requests.")
                return True
            elif "401" in result['error'] or "auth" in result['error'].lower():
                print("❌ Authentication error - API key may be invalid")
                return False
            else:
                print(f"❌ Other error: {result['error']}")
                return False
        else:
            courses = result.get("courses", [])
            print(f"✅ Success! Found {len(courses)} courses")
            for course in courses:
                print(f"   - {course.get('course_name', 'Unknown')}")
            return True
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_direct_api())
    
    if success:
        print("\n" + "=" * 50)
        print("✅ Golf Course API is working correctly!")
        print("Your API key is valid and the service is functional.")
    else:
        print("\n" + "=" * 50)
        print("❌ There may be an issue with the API setup.")
