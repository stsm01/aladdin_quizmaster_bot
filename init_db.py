#!/usr/bin/env python3
"""Initialize the database tables"""

from app.core.database import create_tables, engine
from sqlalchemy import text

def init_database():
    """Initialize database with tables"""
    print("🗄️  Initializing PostgreSQL database...")
    
    # Test connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Create tables
    try:
        create_tables()
        print("✅ Database tables created successfully")
        
        # List created tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename;
            """))
            tables = [row[0] for row in result]
            print(f"📋 Created tables: {', '.join(tables)}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

if __name__ == "__main__":
    init_database()