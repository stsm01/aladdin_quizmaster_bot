#!/usr/bin/env python3
"""
Deployment entry point for the Quiz Bot API.
This script is optimized for deployment and only runs the FastAPI server.
"""

import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    print("🚀 Starting Quiz Bot API for deployment...")
    print(f"📡 API will be available at http://{settings.api_host}:{settings.api_port}")
    
    uvicorn.run(
        "app.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        workers=1
    )