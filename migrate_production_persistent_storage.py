#!/usr/bin/env python3
"""
Migrate persistent storage to production database
"""

import os
import sys
from sqlalchemy import text

# Production database URL
PRODUCTION_DATABASE_URL = "postgresql://neondb_owner:npg_9BH3JEMRwQna@ep-bitter-lake-a69kivks.us-west-2.aws.neon.tech/neondb?sslmode=require"

def migrate_production_storage():
    """Create user_states table in production database"""
    try:
        # Set production database
        os.environ["DATABASE_URL"] = PRODUCTION_DATABASE_URL
        
        print("🚀 Migrating persistent storage to production database...")
        print(f"📍 Target: {PRODUCTION_DATABASE_URL.split('@')[1].split('/')[0]}")
        
        from app.core.database import engine, Base, UserState
        from sqlalchemy.orm import sessionmaker
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Create all tables (will only create missing ones)
            print("🔄 Creating user_states table in production...")
            Base.metadata.create_all(bind=engine)
            
            # Test the connection and table
            result = db.execute(text("SELECT COUNT(*) FROM user_states"))
            count = result.scalar()
            print(f"✅ user_states table created successfully in production")
            print(f"📊 Current user_states count: {count}")
            
            # Test write/read
            print("🧪 Testing table functionality...")
            db.execute(text("""
                INSERT INTO user_states (telegram_id, state, data, updated_at) 
                VALUES (999999999, 'test', '{"test": true}', NOW())
                ON CONFLICT (telegram_id) 
                DO UPDATE SET state = 'test'
            """))
            db.commit()
            
            db.execute(text("DELETE FROM user_states WHERE telegram_id = 999999999"))
            db.commit()
            
            print("✅ Production persistent storage is ready")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error migrating production storage: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = migrate_production_storage()
    if success:
        print("\n🎉 Production migration complete!")
        print("🤖 Ready to deploy bot with persistent storage")
    sys.exit(0 if success else 1)