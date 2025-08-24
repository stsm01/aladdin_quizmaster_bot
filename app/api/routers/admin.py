"""Admin API routes for question management"""

from fastapi import APIRouter, HTTPException, status
from typing import List
from ...core.models import QuestionInput, SuccessResponse, ErrorResponse
from ...core.services import QuestionService

router = APIRouter()

@router.post("/questions/import", response_model=SuccessResponse)
async def import_questions(
    questions: List[QuestionInput]
):
    """
    Import questions from JSON data
    
    Each question must have exactly one correct answer.
    """
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No questions provided"
        )
    
    result = QuestionService.import_questions(questions)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return SuccessResponse(
        success=True,
        message=result["message"]
    )

@router.get("/questions", response_model=List[dict])
async def get_all_questions():
    """Get all questions"""
    questions = QuestionService.get_all_questions()
    
    result = []
    for question in questions:
        question_data = {
            "id": question.id,
            "title": question.title,
            "text": question.text,
            "options": []
        }
        
        for option in question.options:
            question_data["options"].append({
                "id": option.id,
                "text": option.text,
                "is_correct": option.is_correct,
                "comment": option.comment
            })
        
        result.append(question_data)
    
    return result

@router.delete("/questions/clear", response_model=SuccessResponse)
async def clear_questions():
    """Clear all questions"""
    from ...core.storage import storage
    storage.clear_questions()
    
    return SuccessResponse(
        success=True,
        message="All questions cleared successfully"
    )

@router.get("/stats", response_model=dict)
async def get_admin_stats():
    """Get statistics"""
    from ...core.storage import storage
    
    finished_sessions = [s for s in storage.quiz_sessions.values() if s.finished_at is not None]
    active_sessions = [s for s in storage.quiz_sessions.values() if s.finished_at is None]
    
    return {
        "questions_count": len(storage.questions),
        "users_count": len(storage.users),
        "total_sessions": len(storage.quiz_sessions),
        "finished_sessions": len(finished_sessions),
        "active_sessions": len(active_sessions),
        "total_answers": len(storage.user_answers)
    }
