#!/usr/bin/env python3
"""
Setup persistent storage for development environment
"""

import os
import sys
from sqlalchemy import text

def setup_dev_storage():
    """Setup user_states table in dev database"""
    try:
        # Use dev database (not production)
        dev_db_url = os.getenv("DATABASE_URL")
        if not dev_db_url:
            print("❌ No DATABASE_URL found - using development database")
            return False
            
        print(f"🔄 Setting up persistent storage in development database...")
        
        from app.core.database import engine, Base, UserState
        from sqlalchemy.orm import sessionmaker
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Create all tables (will only create missing ones)
            Base.metadata.create_all(bind=engine)
            print("✅ user_states table created in DEV database")
            
            # Test the table
            result = db.execute(text("SELECT COUNT(*) FROM user_states"))
            count = result.scalar()
            print(f"📊 Current user_states count in DEV: {count}")
            
            print("🧪 Development persistent storage is ready for testing")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error setting up dev storage: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = setup_dev_storage()
    sys.exit(0 if success else 1)