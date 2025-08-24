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
    print("🚀 Starting Quiz Bot Application...")
    print(f"📡 API will be available at http://{settings.api_host}:{settings.api_port}")
    print("🤖 Telegram bot is starting...")
    
    # Start API server in a separate process
    api_process = Process(target=run_api)
    api_process.start()
    
    # Wait a bit for API to start
    time.sleep(2)
    
    try:
        # Run bot in main process
        run_bot()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        api_process.terminate()
        api_process.join()
        print("✅ Application stopped")
