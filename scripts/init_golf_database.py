#!/usr/bin/env python3
"""
Initialize golf database tables
"""
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.models.database import engine
from app.models.golf_models import Base

def init_golf_tables():
    """Create golf database tables"""
    try:
        print("🏌️ Creating golf database tables...")
        
        # Create all tables defined in golf_models
        Base.metadata.create_all(bind=engine)
        
        print("✅ Golf database tables created successfully!")
        print("   - golf_courses")
        print("   - golf_holes") 
        print("   - golf_strategies")
        print("   - golf_sessions")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating golf tables: {str(e)}")
        return False

if __name__ == "__main__":
    success = init_golf_tables()
    sys.exit(0 if success else 1)
