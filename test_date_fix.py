#!/usr/bin/env python3
"""
Test script to verify the date fix for factor analysis
"""
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.futureexploratorium.event_analysis_service import FutureExploratoriumEventAnalysisService

async def test_date_fix():
    """Test that the date fix works correctly"""
    print("Testing date fix for factor analysis...")
    
    # Initialize the service
    service = FutureExploratoriumEventAnalysisService()
    
    # Test with different dates
    test_dates = [
        "2025-01-15",
        "2025-02-20", 
        "2025-03-10"
    ]
    
    for date in test_dates:
        print(f"\nTesting with date: {date}")
        try:
            result = await service.generate_diagnostic_event_analysis(date)
            
            if result["success"]:
                print(f"✅ Success for {date}")
                print(f"   Worst week date: {result['worst_week']['date']}")
                print(f"   Requested date: {result.get('requested_date', 'Not set')}")
                print(f"   AI available: {result.get('ai_available', False)}")
                print(f"   Factor count: {len(result.get('factor_impact_table', []))}")
                
                # Check if the date matches
                if result['worst_week']['date'] == date:
                    print(f"   ✅ Date matches requested date")
                else:
                    print(f"   ❌ Date mismatch: expected {date}, got {result['worst_week']['date']}")
            else:
                print(f"❌ Failed for {date}: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception for {date}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_date_fix())
