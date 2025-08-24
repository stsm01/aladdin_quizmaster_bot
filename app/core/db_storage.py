"""PostgreSQL storage implementation"""

import json
import uuid
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from .database import (
    get_db, User as DBUser, Question as DBQuestion, 
    AnswerOption as DBAnswerOption, QuizSession as DBQuizSession, 
    UserAnswer as DBUserAnswer, SessionLocal
)
from .models import QuestionInput

class PostgreSQLStorage:
    """PostgreSQL storage implementation"""
    
    def get_db(self) -> Session:
        """Get database session"""
        return SessionLocal()
    
    # User methods
    def create_or_update_user(self, telegram_id: int, first_name: str, last_name: str) -> DBUser:
        """Create or update user"""
        db = self.get_db()
        try:
            user = db.query(DBUser).filter(DBUser.telegram_id == telegram_id).first()
            if user:
                user.first_name = first_name
                user.last_name = last_name
            else:
                user = DBUser(
                    telegram_id=telegram_id,
                    first_name=first_name,
                    last_name=last_name
                )
                db.add(user)
            db.commit()
            db.refresh(user)
            return user
        finally:
            db.close()
    
    def get_user(self, telegram_id: int) -> Optional[DBUser]:
        """Get user by telegram_id"""
        db = self.get_db()
        try:
            return db.query(DBUser).filter(DBUser.telegram_id == telegram_id).first()
        finally:
            db.close()
    
    # Question methods
    def clear_questions(self):
        """Clear all questions and answer options"""
        db = self.get_db()
        try:
            db.query(DBAnswerOption).delete()
            db.query(DBQuestion).delete()
            db.commit()
        finally:
            db.close()
    
    def add_question(self, question_data: QuestionInput):
        """Add question to storage"""
        db = self.get_db()
        try:
            # Create question
            question = DBQuestion(
                id=question_data.id,
                title=question_data.title,
                text=question_data.text
            )
            db.add(question)
            
            # Create answer options
            for option_data in question_data.answers:
                option = DBAnswerOption(
                    id=option_data.id,
                    question_id=question_data.id,
                    text=option_data.text,
                    is_correct=option_data.is_correct,
                    comment=option_data.comment
                )
                db.add(option)
            
            db.commit()
        finally:
            db.close()
    
    def get_question(self, question_id: str) -> Optional[DBQuestion]:
        """Get question by ID"""
        db = self.get_db()
        try:
            question = db.query(DBQuestion).options(joinedload(DBQuestion.options)).filter(DBQuestion.id == question_id).first()
            return question
        finally:
            db.close()
    
    def get_all_questions(self) -> List[DBQuestion]:
        """Get all questions"""
        db = self.get_db()
        try:
            questions = db.query(DBQuestion).options(joinedload(DBQuestion.options)).all()
            return questions
        finally:
            db.close()
    
    def get_question_options(self, question_id: str) -> List[DBAnswerOption]:
        """Get all options for a question"""
        db = self.get_db()
        try:
            return db.query(DBAnswerOption).filter(DBAnswerOption.question_id == question_id).all()
        finally:
            db.close()
    
    def get_answer_option(self, option_id: str) -> Optional[DBAnswerOption]:
        """Get answer option by ID"""
        db = self.get_db()
        try:
            return db.query(DBAnswerOption).filter(DBAnswerOption.id == option_id).first()
        finally:
            db.close()
    
    # Session methods
    def create_quiz_session(self, user_telegram_id: int, shuffle: bool = True) -> DBQuizSession:
        """Create new quiz session"""
        db = self.get_db()
        try:
            # Get all question IDs
            questions = db.query(DBQuestion).all()
            question_ids = [q.id for q in questions]
            
            if shuffle:
                random.shuffle(question_ids)
            
            session = DBQuizSession(
                id=str(uuid.uuid4()),
                user_telegram_id=user_telegram_id,
                question_order=json.dumps(question_ids),
                total_count=len(question_ids)
            )
            
            db.add(session)
            db.commit()
            db.refresh(session)
            return session
        finally:
            db.close()
    
    def get_quiz_session(self, session_id: str) -> Optional[DBQuizSession]:
        """Get quiz session by ID"""
        db = self.get_db()
        try:
            return db.query(DBQuizSession).filter(DBQuizSession.id == session_id).first()
        finally:
            db.close()
    
    def update_quiz_session(self, session_id: str, **updates):
        """Update quiz session"""
        db = self.get_db()
        try:
            db.query(DBQuizSession).filter(DBQuizSession.id == session_id).update(updates)
            db.commit()
        finally:
            db.close()
    
    def finish_quiz_session(self, session_id: str) -> Optional[DBQuizSession]:
        """Mark session as finished"""
        db = self.get_db()
        try:
            session = db.query(DBQuizSession).filter(DBQuizSession.id == session_id).first()
            if session:
                session.finished_at = datetime.now()
                db.commit()
                db.refresh(session)
            return session
        finally:
            db.close()
    
    # Answer methods
    def add_user_answer(self, session_id: str, user_telegram_id: int, question_id: str, 
                       chosen_option_id: str, is_correct: bool):
        """Add user answer"""
        db = self.get_db()
        try:
            answer = DBUserAnswer(
                session_id=session_id,
                user_telegram_id=user_telegram_id,
                question_id=question_id,
                chosen_option_id=chosen_option_id,
                is_correct=is_correct
            )
            db.add(answer)
            
            # Update session correct count if answer is correct
            if is_correct:
                session = db.query(DBQuizSession).filter(DBQuizSession.id == session_id).first()
                if session:
                    session.correct_count += 1
            
            db.commit()
        finally:
            db.close()
    
    def get_user_sessions(self, telegram_id: int) -> List[DBQuizSession]:
        """Get all sessions for a user"""
        db = self.get_db()
        try:
            return db.query(DBQuizSession).filter(
                DBQuizSession.user_telegram_id == telegram_id
            ).order_by(desc(DBQuizSession.started_at)).all()
        finally:
            db.close()
    
    def get_user_stats(self, telegram_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        db = self.get_db()
        try:
            user = db.query(DBUser).filter(DBUser.telegram_id == telegram_id).first()
            if not user:
                return {}
            
            sessions = db.query(DBQuizSession).filter(
                DBQuizSession.user_telegram_id == telegram_id,
                DBQuizSession.finished_at.isnot(None)
            ).order_by(desc(DBQuizSession.started_at)).all()
            
            if not sessions:
                return {
                    "telegram_id": telegram_id,
                    "full_name": user.full_name,
                    "registered_at": user.registered_at.isoformat(),
                    "attempts": 0,
                    "last_score_percent": 0,
                    "best_score_percent": 0
                }
            
            # Calculate scores
            scores = []
            for session in sessions:
                if session.total_count > 0:
                    score = (session.correct_count / session.total_count) * 100
                    scores.append(score)
            
            last_score = scores[0] if scores else 0  # First is latest due to ORDER BY DESC
            best_score = max(scores) if scores else 0
            
            return {
                "telegram_id": telegram_id,
                "full_name": user.full_name,
                "registered_at": user.registered_at.isoformat(),
                "attempts": len(sessions),
                "last_score_percent": round(last_score, 1),
                "best_score_percent": round(best_score, 1)
            }
        finally:
            db.close()

# Global storage instance
storage = PostgreSQLStorage()