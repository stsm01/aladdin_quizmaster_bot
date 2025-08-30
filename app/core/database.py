"""Database models and connection setup"""

import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env early
load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Engine configuration with SSL handling
engine_kwargs = {
    "pool_pre_ping": True,  # Verify connections before use
    "pool_recycle": 300,    # Recycle connections every 5 minutes
}

# Add SSL configuration for production
if DATABASE_URL and "postgresql" in DATABASE_URL:
    engine_kwargs.update({
        "connect_args": {
            "sslmode": "prefer",
            "connect_timeout": 10,
            "application_name": "quiz_bot_app"
        }
    })

# Create engine and session
engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Database Models
class Test(Base):
    __tablename__ = "tests"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    questions = relationship("Question", back_populates="test", cascade="all, delete-orphan")
    sessions = relationship("QuizSession", back_populates="test")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sessions = relationship("QuizSession", back_populates="user")
    answers = relationship("UserAnswer", back_populates="user")
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(String, primary_key=True)
    test_id = Column(String, ForeignKey("tests.id"), nullable=False)
    title = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    test = relationship("Test", back_populates="questions")
    options = relationship("AnswerOption", back_populates="question", cascade="all, delete-orphan")

class AnswerOption(Base):
    __tablename__ = "answer_options"
    
    id = Column(String, primary_key=True)
    question_id = Column(String, ForeignKey("questions.id"), nullable=False)
    text = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    comment = Column(Text, nullable=False)
    
    # Relationships
    question = relationship("Question", back_populates="options")

class QuizSession(Base):
    __tablename__ = "quiz_sessions"
    
    id = Column(String, primary_key=True)
    user_telegram_id = Column(Integer, ForeignKey("users.telegram_id"), nullable=False)
    test_id = Column(String, ForeignKey("tests.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    question_order = Column(Text, nullable=False)  # JSON string of question IDs
    current_question_index = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    total_count = Column(Integer, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    test = relationship("Test", back_populates="sessions")
    answers = relationship("UserAnswer", back_populates="session")

class UserAnswer(Base):
    __tablename__ = "user_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("quiz_sessions.id"), nullable=False)
    user_telegram_id = Column(Integer, ForeignKey("users.telegram_id"), nullable=False)
    question_id = Column(String, nullable=False)
    chosen_option_id = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("QuizSession", back_populates="answers")
    user = relationship("User", back_populates="answers")

class UserState(Base):
    __tablename__ = "user_states"
    
    telegram_id = Column(Integer, primary_key=True, index=True)
    state = Column(String, nullable=True)  # aiogram state name
    data = Column(Text, nullable=True)  # JSON string with state data
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all database tables"""
    Base.metadata.drop_all(bind=engine)