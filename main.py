#!/usr/bin/env python3
"""
Main entry point for the Quiz Bot application.
Runs both the FastAPI server and Telegram bot concurrently.
"""

import asyncio
import uvicorn
from multiprocessing import Process
import time
import sys
import os

from app.core.config import settings
from app.api.main import app
from app.bot.bot import main as bot_main

def run_api():
    """Run FastAPI server"""
    uvicorn.run(
        "app.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False
    )

def run_bot():
    """Run Telegram bot"""
    asyncio.run(bot_main())

if __name__ == "__main__":
    print("🚀 Starting Quiz Bot API...")
    print(f"📡 API will be available at http://{settings.api_host}:{settings.api_port}")
    print("🌐 Running in API-only mode (Bot disabled)")
    
    try:
        # Run only API server
        run_api()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        print("✅ Application stopped")
