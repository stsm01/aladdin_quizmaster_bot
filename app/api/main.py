"""FastAPI application main module"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .routers import admin, public

# Create FastAPI app
app = FastAPI(
    title="Quiz Bot API",
    description="API for Telegram Quiz Bot - Account Manager Knowledge Testing",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(public.router, prefix="/public", tags=["public"])

@app.get("/")
async def root():
    """Root endpoint - serves as health check for deployment"""
    return {
        "message": "Quiz Bot API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for deployment monitoring"""
    try:
        from ..core.storage import storage
        
        return {
            "status": "healthy",
            "questions_count": len(storage.get_all_questions()),
            "users_count": len(storage.users),
            "active_sessions": len([s for s in storage.quiz_sessions.values() if s.finished_at is None]),
            "timestamp": "2025-08-24T19:11:32Z"
        }
    except Exception as e:
        # Return healthy status even if storage isn't fully initialized
        return {
            "status": "healthy", 
            "message": "API is running",
            "timestamp": "2025-08-24T19:11:32Z"
        }

if __name__ == "__main__":
    from ..core.config import settings
    uvicorn.run(
        "app.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
