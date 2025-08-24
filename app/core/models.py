"""Pydantic models for API requests and responses"""

from typing import List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

# Question models
class AnswerOptionInput(BaseModel):
    """Input model for answer option"""
    id: str = Field(..., alias="ID ответа")
    text: str = Field(..., alias="Текст ответа")
    is_correct: bool = Field(..., alias="Правильный-неправильный ответ")
    comment: str = Field(..., alias="Комментарий к ответу")

class QuestionInput(BaseModel):
    """Input model for question from JSON import"""
    id: str = Field(..., alias="ID вопроса")
    title: str = Field(..., alias="Формулировка вопроса")
    text: str = Field(..., alias="Текст вопроса")
    answers: List[AnswerOptionInput] = Field(..., alias="Ответы")

class QuestionResponse(BaseModel):
    """Response model for question"""
    id: str
    title: str
    text: str
    options: List[dict]

# Session models
class SessionStartRequest(BaseModel):
    """Request to start a new quiz session"""
    telegram_id: int
    shuffle: bool = True

class SessionStartResponse(BaseModel):
    """Response for session start"""
    session_id: str
    total: int

class QuestionWithOptions(BaseModel):
    """Question with answer options for quiz"""
    question_id: str
    title: str
    text: str
    options: List[dict]  # {"id": str, "text": str}
    current: int
    total: int

class AnswerRequest(BaseModel):
    """Request to submit an answer"""
    option_id: str

class AnswerResponse(BaseModel):
    """Response after submitting an answer"""
    is_correct: bool
    comment: str
    progress: dict  # {"current": int, "total": int, "correct": int}

class FinishResponse(BaseModel):
    """Response when finishing a quiz"""
    score_percent: float
    correct_count: int
    total_count: int
    session_id: str

# User models
class UserStats(BaseModel):
    """User statistics response"""
    telegram_id: int
    full_name: str
    registered_at: str
    attempts: int
    last_score_percent: float
    best_score_percent: float

# Generic responses
class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool
    message: str

class ErrorResponse(BaseModel):
    """Generic error response"""
    error: str
    detail: Optional[str] = None
