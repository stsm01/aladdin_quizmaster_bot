"""Public API routes for quiz functionality"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional, List

from ...core.models import (
    SessionStartRequest, SessionStartResponse, QuestionWithOptions,
    AnswerRequest, AnswerResponse, FinishResponse, UserStats,
    UserRegisterRequest, TestResponse
)
from ...core.services import UserService, QuizService, TestService

router = APIRouter()

@router.get("/tests", response_model=List[TestResponse])
async def get_available_tests():
    """Get all available tests"""
    tests = TestService.get_all_tests()
    result = []
    for test in tests:
        questions_count = len(TestService.get_questions_by_test(test.id))
        result.append(TestResponse(
            id=test.id,
            name=test.name,
            description=test.description,
            questions_count=questions_count,
            created_at=test.created_at.isoformat()
        ))
    return result

@router.get("/users/{telegram_id}/stats", response_model=UserStats)
async def get_user_stats(telegram_id: int):
    """Get user statistics"""
    stats = UserService.get_user_stats(telegram_id)
    
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserStats(**stats)

@router.post("/users/register")
async def register_user(request: UserRegisterRequest):
    """Register or update user"""
    user = UserService.create_or_update_user(
        request.telegram_id, 
        request.first_name, 
        request.last_name
    )
    
    return {
        "success": True,
        "message": f"User {user.full_name} registered successfully",
        "telegram_id": user.telegram_id
    }

@router.post("/sessions/start", response_model=SessionStartResponse)
async def start_session(request: SessionStartRequest):
    """Start a new quiz session"""
    result = QuizService.start_session(request)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return SessionStartResponse(
        session_id=result["session_id"],
        total=result["total"]
    )

@router.get("/sessions/{session_id}/next")
async def get_next_question(session_id: str):
    """Get next question for session"""
    question_data = QuizService.get_next_question(session_id)
    
    if question_data is None:
        # No more questions or session not found
        return None
    
    return QuestionWithOptions(**question_data)

@router.post("/sessions/{session_id}/answer", response_model=AnswerResponse)
async def submit_answer(session_id: str, request: AnswerRequest):
    """Submit an answer for the current question"""
    result = QuizService.submit_answer(session_id, request)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return AnswerResponse(
        is_correct=result["is_correct"],
        comment=result["comment"],
        progress=result["progress"]
    )

@router.post("/sessions/{session_id}/finish", response_model=FinishResponse)
async def finish_session(session_id: str):
    """Finish a quiz session and get final results"""
    result = QuizService.finish_session(session_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return FinishResponse(
        score_percent=result["score_percent"],
        correct_count=result["correct_count"],
        total_count=result["total_count"],
        session_id=result["session_id"]
    )

@router.get("/sessions/{session_id}")
async def get_session_info(session_id: str):
    """Get session information"""
    session = QuizService.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return {
        "session_id": session.id,
        "user_id": session.user_id,
        "started_at": session.started_at.isoformat(),
        "finished_at": session.finished_at.isoformat() if session.finished_at else None,
        "current_question": session.current_question_index + 1,
        "total_questions": session.total_count,
        "correct_count": session.correct_count,
        "is_finished": session.finished_at is not None
    }
