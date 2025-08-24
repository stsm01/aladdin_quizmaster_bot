"""In-memory storage for MVP implementation"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
import json
import random

@dataclass
class User:
    telegram_id: int
    first_name: str
    last_name: str
    registered_at: datetime = field(default_factory=datetime.now)
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

@dataclass
class Question:
    id: str
    title: str
    text: str
    options: List['AnswerOption'] = field(default_factory=list)

@dataclass
class AnswerOption:
    id: str
    question_id: str
    text: str
    is_correct: bool
    comment: str

@dataclass
class QuizSession:
    id: str
    user_id: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    question_order: List[str] = field(default_factory=list)
    current_question_index: int = 0
    correct_count: int = 0
    total_count: int = 0
    answers: List['UserAnswer'] = field(default_factory=list)

@dataclass
class UserAnswer:
    session_id: str
    user_id: int
    question_id: str
    chosen_option_id: str
    is_correct: bool
    answered_at: datetime = field(default_factory=datetime.now)

class InMemoryStorage:
    """Simple in-memory storage for the MVP"""
    
    def __init__(self):
        self.users: Dict[int, User] = {}  # telegram_id -> User
        self.questions: Dict[str, Question] = {}  # question_id -> Question
        self.answer_options: Dict[str, AnswerOption] = {}  # option_id -> AnswerOption
        self.quiz_sessions: Dict[str, QuizSession] = {}  # session_id -> QuizSession
        self.user_answers: List[UserAnswer] = []
        
    # User methods
    def create_or_update_user(self, telegram_id: int, first_name: str, last_name: str) -> User:
        """Create or update user"""
        if telegram_id in self.users:
            user = self.users[telegram_id]
            user.first_name = first_name
            user.last_name = last_name
        else:
            user = User(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name
            )
            self.users[telegram_id] = user
        return user
    
    def get_user(self, telegram_id: int) -> Optional[User]:
        """Get user by telegram_id"""
        return self.users.get(telegram_id)
    
    # Question methods
    def clear_questions(self):
        """Clear all questions and answer options"""
        self.questions.clear()
        self.answer_options.clear()
    
    def add_question(self, question: Question):
        """Add question to storage"""
        self.questions[question.id] = question
        for option in question.options:
            self.answer_options[option.id] = option
    
    def get_question(self, question_id: str) -> Optional[Question]:
        """Get question by ID"""
        return self.questions.get(question_id)
    
    def get_all_questions(self) -> List[Question]:
        """Get all questions"""
        return list(self.questions.values())
    
    def get_question_options(self, question_id: str) -> List[AnswerOption]:
        """Get all options for a question"""
        return [opt for opt in self.answer_options.values() if opt.question_id == question_id]
    
    def get_answer_option(self, option_id: str) -> Optional[AnswerOption]:
        """Get answer option by ID"""
        return self.answer_options.get(option_id)
    
    # Session methods
    def create_quiz_session(self, user_id: int, shuffle: bool = True) -> QuizSession:
        """Create new quiz session"""
        session_id = str(uuid.uuid4())
        question_ids = list(self.questions.keys())
        
        if shuffle:
            random.shuffle(question_ids)
        
        session = QuizSession(
            id=session_id,
            user_id=user_id,
            started_at=datetime.now(),
            question_order=question_ids,
            total_count=len(question_ids)
        )
        
        self.quiz_sessions[session_id] = session
        return session
    
    def get_quiz_session(self, session_id: str) -> Optional[QuizSession]:
        """Get quiz session by ID"""
        return self.quiz_sessions.get(session_id)
    
    def update_quiz_session(self, session: QuizSession):
        """Update quiz session"""
        self.quiz_sessions[session.id] = session
    
    def finish_quiz_session(self, session_id: str) -> Optional[QuizSession]:
        """Mark session as finished"""
        session = self.quiz_sessions.get(session_id)
        if session:
            session.finished_at = datetime.now()
        return session
    
    # Answer methods
    def add_user_answer(self, answer: UserAnswer):
        """Add user answer"""
        self.user_answers.append(answer)
        
        # Update session correct count
        session = self.quiz_sessions.get(answer.session_id)
        if session and answer.is_correct:
            session.correct_count += 1
    
    def get_user_sessions(self, telegram_id: int) -> List[QuizSession]:
        """Get all sessions for a user"""
        return [s for s in self.quiz_sessions.values() if s.user_id == telegram_id]
    
    def get_user_stats(self, telegram_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        user = self.get_user(telegram_id)
        if not user:
            return {}
        
        sessions = self.get_user_sessions(telegram_id)
        finished_sessions = [s for s in sessions if s.finished_at is not None]
        
        if not finished_sessions:
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
        for session in finished_sessions:
            if session.total_count > 0:
                score = (session.correct_count / session.total_count) * 100
                scores.append(score)
        
        last_score = scores[-1] if scores else 0
        best_score = max(scores) if scores else 0
        
        return {
            "telegram_id": telegram_id,
            "full_name": user.full_name,
            "registered_at": user.registered_at.isoformat(),
            "attempts": len(finished_sessions),
            "last_score_percent": round(last_score, 1),
            "best_score_percent": round(best_score, 1)
        }

# Global storage instance
storage = InMemoryStorage()
