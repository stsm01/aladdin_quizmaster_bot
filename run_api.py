#!/usr/bin/env python3
"""
Standalone script to run only the FastAPI server
"""

import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    print(f"🚀 Starting Quiz Bot API on {settings.api_host}:{settings.api_port}")
    
    uvicorn.run(
        "app.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False
    )
