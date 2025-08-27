"""Persistent FSM storage implementation for aiogram using PostgreSQL"""

import json
import logging
from typing import Dict, Any, Optional, Set
from aiogram.fsm.storage.base import BaseStorage, StorageKey, StateType
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from ..core.database import UserState

logger = logging.getLogger(__name__)

class PostgreSQLStorage(BaseStorage):
    """PostgreSQL-based storage for aiogram FSM states"""
    
    def __init__(self):
        """Initialize PostgreSQL storage"""
        # Get database URL from environment
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # Create engine and session
        self.engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={
                "sslmode": "prefer",
                "connect_timeout": 10,
                "application_name": "quiz_bot_storage"
            } if "postgresql" in database_url else {}
        )
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables if they don't exist
        from ..core.database import Base
        Base.metadata.create_all(bind=self.engine)
    
    def _get_db(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        """Set user state"""
        try:
            db = self._get_db()
            try:
                # Get or create user state record
                user_state = db.query(UserState).filter(
                    UserState.telegram_id == key.user_id
                ).first()
                
                if user_state is None:
                    user_state = UserState(telegram_id=key.user_id)
                    db.add(user_state)
                
                # Set state
                user_state.state = state.state if state else None
                
                db.commit()
                logger.debug(f"Set state for user {key.user_id}: {state}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error setting state for user {key.user_id}: {e}")
    
    async def get_state(self, key: StorageKey) -> Optional[str]:
        """Get user state"""
        try:
            db = self._get_db()
            try:
                user_state = db.query(UserState).filter(
                    UserState.telegram_id == key.user_id
                ).first()
                
                if user_state:
                    return user_state.state
                return None
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error getting state for user {key.user_id}: {e}")
            return None
    
    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        """Set user data"""
        try:
            db = self._get_db()
            try:
                # Get or create user state record
                user_state = db.query(UserState).filter(
                    UserState.telegram_id == key.user_id
                ).first()
                
                if user_state is None:
                    user_state = UserState(telegram_id=key.user_id)
                    db.add(user_state)
                
                # Set data as JSON
                user_state.data = json.dumps(data) if data else None
                
                db.commit()
                logger.debug(f"Set data for user {key.user_id}: {data}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error setting data for user {key.user_id}: {e}")
    
    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        """Get user data"""
        try:
            db = self._get_db()
            try:
                user_state = db.query(UserState).filter(
                    UserState.telegram_id == key.user_id
                ).first()
                
                if user_state and user_state.data:
                    return json.loads(user_state.data)
                return {}
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error getting data for user {key.user_id}: {e}")
            return {}
    
    async def update_data(self, key: StorageKey, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user data"""
        current_data = await self.get_data(key)
        current_data.update(data)
        await self.set_data(key, current_data)
        return current_data
    
    async def close(self) -> None:
        """Close storage connections"""
        self.engine.dispose()
    
    async def wait_closed(self) -> None:
        """Wait for storage to be closed"""
        pass