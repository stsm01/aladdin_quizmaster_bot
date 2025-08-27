#!/usr/bin/env python3
"""
Check quiz sessions in database
"""

import os
import json
from sqlalchemy import text

def check_quiz_sessions():
    """Check current quiz sessions in database"""
    try:
        from app.core.database import SessionLocal
        
        print("🔍 Checking quiz sessions in database...")
        
        # Create session
        db = SessionLocal()
        
        try:
            # Get all quiz sessions
            result = db.execute(text("""
                SELECT id, user_telegram_id, test_id, started_at, finished_at, 
                       question_order, current_question_index, correct_count, total_count
                FROM quiz_sessions 
                ORDER BY started_at DESC
            """))
            sessions = result.fetchall()
            
            print(f"📊 Found {len(sessions)} quiz sessions:")
            
            for session in sessions:
                (session_id, user_id, test_id, started_at, finished_at, 
                 question_order, current_index, correct_count, total_count) = session
                
                # Parse question order if exists
                questions = []
                if question_order:
                    try:
                        questions = json.loads(question_order)
                    except:
                        questions = ["Invalid JSON"]
                
                print(f"  📝 Session {session_id[:8]}...")
                print(f"     User: {user_id}")
                print(f"     Test: {test_id}")
                print(f"     Started: {started_at}")
                print(f"     Finished: {finished_at or 'Active'}")
                print(f"     Progress: {current_index}/{total_count}")
                print(f"     Correct: {correct_count}")
                print(f"     Questions order: {questions[:3]}{'...' if len(questions) > 3 else ''}")
                
                # Current question info
                if current_index < len(questions) and not finished_at:
                    print(f"     Current question: {questions[current_index]} (index {current_index})")
                
                print()
                
            if len(sessions) == 0:
                print("  ℹ️  No quiz sessions found yet")
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error checking quiz sessions: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_quiz_sessions()