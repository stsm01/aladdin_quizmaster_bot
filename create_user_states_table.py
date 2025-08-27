#!/usr/bin/env python3
"""
Create user_states table in database
"""

import os
import sys
from sqlalchemy import text

# Set production database
PRODUCTION_DATABASE_URL = "postgresql://neondb_owner:npg_9BH3JEMRwQna@ep-bitter-lake-a69kivks.us-west-2.aws.neon.tech/neondb?sslmode=require"
os.environ["DATABASE_URL"] = PRODUCTION_DATABASE_URL

def create_user_states_table():
    """Create user_states table if not exists"""
    try:
        from app.core.database import engine, Base, UserState
        from sqlalchemy.orm import sessionmaker
        
        print("🔄 Creating user_states table...")
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Create all tables (will only create missing ones)
            Base.metadata.create_all(bind=engine)
            print("✅ user_states table created successfully")
            
            # Test the table
            result = db.execute(text("SELECT COUNT(*) FROM user_states"))
            count = result.scalar()
            print(f"📊 Current user_states count: {count}")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error creating user_states table: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = create_user_states_table()
    sys.exit(0 if success else 1)