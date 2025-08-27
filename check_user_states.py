#!/usr/bin/env python3
"""
Check user states in database for testing persistent storage
"""

import os
import json
from sqlalchemy import text

def check_user_states():
    """Check current user states in database"""
    try:
        from app.core.database import SessionLocal
        
        print("🔍 Checking user states in database...")
        
        # Create session
        db = SessionLocal()
        
        try:
            # Get all user states
            result = db.execute(text("SELECT telegram_id, state, data, updated_at FROM user_states ORDER BY updated_at DESC"))
            states = result.fetchall()
            
            print(f"📊 Found {len(states)} user states:")
            
            for state in states:
                telegram_id, state_name, data_json, updated_at = state
                
                # Parse data if exists
                data = {}
                if data_json:
                    try:
                        data = json.loads(data_json)
                    except:
                        data = {"error": "Invalid JSON"}
                
                print(f"  👤 User {telegram_id}:")
                print(f"     State: {state_name or 'None'}")
                print(f"     Data: {data}")
                print(f"     Updated: {updated_at}")
                print()
                
            if len(states) == 0:
                print("  ℹ️  No user states found yet")
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error checking user states: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_user_states()