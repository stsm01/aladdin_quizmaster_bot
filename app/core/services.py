"""Business logic services"""

from typing import List, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .database import QuizSession
from .db_storage import storage
from .models import QuestionInput, SessionStartRequest, AnswerRequest
from .storage import Test
import uuid
import json
from datetime import datetime

class UserService:
    """Service for user management"""
    
    @staticmethod
    def create_or_update_user(telegram_id: int, first_name: str, last_name: str):
        """Create or update user"""
        return storage.create_or_update_user(telegram_id, first_name, last_name)
    
    @staticmethod
    def get_user(telegram_id: int):
        """Get user by telegram ID"""
        return storage.get_user(telegram_id)
    
    @staticmethod
    def get_user_stats(telegram_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        return storage.get_user_stats(telegram_id)

class QuestionService:
    """Service for question management"""
    
    @staticmethod
    def import_questions(questions_data: List[QuestionInput], test_id: str = None) -> Dict[str, Any]:
        """Import questions from JSON data"""
        try:
            # If no test_id provided, create a default test or use existing logic
            if not test_id:
                # Legacy mode - for backward compatibility
                storage.clear_questions()
                
                # Check if default test exists, create if not
                default_test = storage.get_test("default")
                if not default_test:
                    default_test = Test(
                        id="default",
                        name="Imported Questions",
                        description="Questions imported without specific test assignment"
                    )
                    storage.create_test(default_test)
                test_id = "default"
            
            # Check if test exists
            test = storage.get_test(test_id)
            if not test:
                return {
                    "success": False,
                    "error": f"Test with ID {test_id} not found"
                }
            
            imported_count = 0
            for q_data in questions_data:
                # Validate that exactly one answer is correct
                correct_answers = [ans for ans in q_data.answers if ans.is_correct]
                if len(correct_answers) != 1:
                    return {
                        "success": False,
                        "error": f"Question {q_data.id} must have exactly one correct answer"
                    }
                
                # Add question to storage with test_id
                storage.add_question(q_data, test_id)
                imported_count += 1
            
            return {
                "success": True,
                "message": f"Successfully imported {imported_count} questions to test '{test.name}'"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error importing questions: {str(e)}"
            }
    
    @staticmethod
    def get_all_questions():
        """Get all questions"""
        return storage.get_all_questions()
    
    @staticmethod
    def get_question(question_id: str):
        """Get question by ID"""
        return storage.get_question(question_id)
    
    @staticmethod
    def get_question_options(question_id: str):
        """Get options for a question"""
        return storage.get_question_options(question_id)

class TestService:
    """Service for test management"""
    
    @staticmethod
    def create_test(name: str, description: str = ""):
        """Create a new test"""
        test_id = str(uuid.uuid4())
        return storage.create_test(test_id, name, description)
    
    @staticmethod
    def get_test(test_id: str):
        """Get test by ID"""
        return storage.get_test(test_id)
    
    @staticmethod
    def get_all_tests():
        """Get all tests"""
        return storage.get_all_tests()
    
    @staticmethod
    def get_questions_by_test(test_id: str):
        """Get all questions for a specific test"""
        return storage.get_questions_by_test(test_id)

class QuizService:
    """Service for quiz session management"""
    
    @staticmethod
    def start_session(request: SessionStartRequest) -> Dict[str, Any]:
        """Start a new quiz session"""
        # Check if user exists
        user = storage.get_user(request.telegram_id)
        if not user:
            return {
                "success": False,
                "error": "User not found. Please register first."
            }
        
        # Check if test exists
        test = storage.get_test(request.test_id)
        if not test:
            return {
                "success": False,
                "error": f"Test with ID {request.test_id} not found."
            }
        
        # Check if questions exist for this test
        questions = storage.get_questions_by_test(request.test_id)
        if not questions:
            return {
                "success": False,
                "error": f"No questions available for test '{test.name}'. Please import questions first."
            }
        
        # Create session  
        session = storage.create_quiz_session(request.telegram_id, request.test_id, request.shuffle)
        
        return {
            "success": True,
            "session_id": session.id,
            "total": session.total_count
        }
    
    @staticmethod
    def get_next_question(session_id: str) -> Optional[Dict[str, Any]]:
        """Get next question for session"""
        session = storage.get_quiz_session(session_id)
        if not session:
            return None
        
        # Check if session is finished
        question_order = json.loads(session.question_order)
        if session.current_question_index >= len(question_order):
            return None
        
        question_id = question_order[session.current_question_index]
        question = storage.get_question(question_id)
        if not question:
            return None
        
        # Prepare options without revealing correct answer
        options = []
        for option in question.options:
            options.append({
                "id": option.id,
                "text": option.text
            })
        
        return {
            "question_id": question.id,
            "title": question.title,
            "text": question.text,
            "options": options,
            "current": session.current_question_index + 1,
            "total": session.total_count
        }
    
    @staticmethod
    def submit_answer(session_id: str, request: AnswerRequest) -> Dict[str, Any]:
        """Submit an answer for a question"""
        session = storage.get_quiz_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}
        
        # Get current question
        question_order = json.loads(session.question_order)
        if session.current_question_index >= len(question_order):
            return {"success": False, "error": "No more questions in this session"}
        
        question_id = question_order[session.current_question_index]
        option = storage.get_answer_option(request.option_id)
        
        if not option or option.question_id != question_id:
            return {"success": False, "error": "Invalid answer option"}
        
        # Record answer (this updates correct_count automatically)
        storage.add_user_answer(
            session_id=session.id,
            user_telegram_id=session.user_telegram_id,
            question_id=question_id,
            chosen_option_id=request.option_id,
            is_correct=option.is_correct
        )
        
        # Get updated session data after recording answer
        updated_session = storage.get_quiz_session(session_id)
        
        # Move to next question
        new_question_index = session.current_question_index + 1
        storage.update_quiz_session(session_id, current_question_index=new_question_index)
        
        return {
            "success": True,
            "is_correct": option.is_correct,
            "comment": option.comment,
            "progress": {
                "current": new_question_index,  # Number of completed questions
                "total": session.total_count,
                "correct": updated_session.correct_count  # Updated count after answer
            }
        }
    
    @staticmethod
    def finish_session(session_id: str) -> Dict[str, Any]:
        """Finish a quiz session"""
        session = storage.finish_quiz_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}
        
        score_percent = 0
        if session.total_count > 0:
            score_percent = (session.correct_count / session.total_count) * 100
        
        return {
            "success": True,
            "score_percent": round(score_percent, 1),
            "correct_count": session.correct_count,
            "total_count": session.total_count,
            "session_id": session.id
        }
    
    @staticmethod
    def get_session(session_id: str):
        """Get session by ID"""
        return storage.get_quiz_session(session_id)
