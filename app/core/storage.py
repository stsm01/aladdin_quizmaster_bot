"""In-memory storage for MVP implementation"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
import json
import random

@dataclass
class Test:
    id: str
    name: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)

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
    test_id: str
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
    test_id: str
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
        self.tests: Dict[str, Test] = {}  # test_id -> Test  
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
    
    # Test methods
    def create_test(self, test: Test) -> Test:
        """Create a new test"""
        self.tests[test.id] = test
        return test
    
    def get_test(self, test_id: str) -> Optional[Test]:
        """Get test by ID"""
        return self.tests.get(test_id)
    
    def get_all_tests(self) -> List[Test]:
        """Get all tests"""
        return list(self.tests.values())
    
    # Question methods
    def clear_questions(self):
        """Clear all questions and answer options"""
        self.questions.clear()
        self.answer_options.clear()
    
    def add_question(self, question_data, test_id: str = None):
        """Add question to storage"""
        # Convert QuestionInput to Question if needed
        if hasattr(question_data, 'id'):  # It's a QuestionInput
            # Create AnswerOption objects
            options = []
            for opt_data in question_data.answers:
                option = AnswerOption(
                    id=opt_data.id,
                    question_id=question_data.id,
                    text=opt_data.text,
                    is_correct=opt_data.is_correct,
                    comment=opt_data.comment
                )
                options.append(option)
                self.answer_options[option.id] = option
            
            # Create Question object
            question = Question(
                id=question_data.id,
                test_id=test_id or "default",
                title=question_data.title,
                text=question_data.text,
                options=options
            )
            self.questions[question.id] = question
        else:  # It's already a Question object
            self.questions[question_data.id] = question_data
            for option in question_data.options:
                self.answer_options[option.id] = option
    
    def get_questions_by_test(self, test_id: str) -> List[Question]:
        """Get all questions for a specific test"""
        return [q for q in self.questions.values() if q.test_id == test_id]
    
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
    def create_quiz_session(self, user_id: int, test_id: str, shuffle: bool = True) -> QuizSession:
        """Create new quiz session"""
        session_id = str(uuid.uuid4())
        test_questions = self.get_questions_by_test(test_id)
        question_ids = [q.id for q in test_questions]
        
        if shuffle:
            random.shuffle(question_ids)
        
        session = QuizSession(
            id=session_id,
            user_id=user_id,
            test_id=test_id,
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
    
    # Test methods
    def create_test(self, test_id: str, name: str, description: str = "") -> Test:
        """Create a new test"""
        test = Test(
            id=test_id,
            name=name,
            description=description
        )
        self.tests[test_id] = test
        return test
    
    def get_test(self, test_id: str) -> Optional[Test]:
        """Get test by ID"""
        return self.tests.get(test_id)
    
    def get_all_tests(self) -> List[Test]:
        """Get all tests"""
        return list(self.tests.values())

# Global storage instance
storage = InMemoryStorage()
