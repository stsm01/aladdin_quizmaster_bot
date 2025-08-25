#!/usr/bin/env python3
"""
Deployment entry point for Quiz Bot
Runs both API and Telegram bot for deployment
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
        host="0.0.0.0",
        port=5000,
        reload=False,
        workers=1,
        log_level="info"
    )

def run_bot():
    """Run Telegram bot"""
    asyncio.run(bot_main())

if __name__ == "__main__":
    print("🚀 Starting Quiz Bot for deployment...")
    print("📡 API will be available at http://0.0.0.0:5000")
    print("🤖 Telegram bot is starting...")
    
    # Start API server in a separate process
    api_process = Process(target=run_api)
    api_process.start()
    
    # Wait a bit for API to start
    time.sleep(3)
    
    try:
        # Run bot in main process
        run_bot()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        api_process.terminate()
        api_process.join()
        print("✅ Application stopped")