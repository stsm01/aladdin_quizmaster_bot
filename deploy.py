#!/usr/bin/env python3
"""
Deployment entry point for Quiz Bot
Optimized for Replit deployments - runs FastAPI with background bot task
"""

import asyncio
import uvicorn
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.main import app
from app.bot.bot import main as bot_main

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Background task for bot
bot_task = None

async def start_bot():
    """Start the Telegram bot as a background task"""
    global bot_task
    try:
        logger.info("🤖 Starting Telegram bot in background...")
        bot_task = asyncio.create_task(bot_main())
        await bot_task
    except asyncio.CancelledError:
        logger.info("🤖 Bot task cancelled")
    except Exception as e:
        logger.error(f"🤖 Bot error: {e}")

@asynccontextmanager
async def lifespan(app):
    """Lifespan manager for FastAPI app"""
    global bot_task
    
    # Startup
    logger.info("🚀 Starting Quiz Bot for deployment...")
    logger.info("📡 API server is starting...")
    
    # Only start bot if token is configured
    if settings.bot_token and settings.bot_token != "your_bot_token_here":
        logger.info("🤖 Starting Telegram bot...")
        bot_task = asyncio.create_task(start_bot())
    else:
        logger.warning("⚠️ Bot token not configured, running in API-only mode")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    if bot_task:
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass
    logger.info("✅ Application stopped")

# Create new app instance with lifespan
from fastapi import FastAPI

# Create the app with proper lifespan
deployment_app = FastAPI(
    title="Telegram Quiz Bot API",
    description="API for Telegram Quiz Bot with integrated bot polling",
    version="1.0.0",
    lifespan=lifespan
)

# Include all routers from original app
from app.api.routers.public import router as public_router
from app.api.routers.admin import router as admin_router

deployment_app.include_router(public_router, prefix="/public", tags=["public"])
deployment_app.include_router(admin_router, prefix="/admin", tags=["admin"])

@deployment_app.get("/")
async def root():
    return {"message": "Telegram Quiz Bot API is running", "status": "ok"}

@deployment_app.get("/health")
async def health():
    return {"status": "healthy", "bot": "running" if bot_task else "not_configured"}

# Use deployment_app instead of original app
app = deployment_app

if __name__ == "__main__":
    print("🚀 Starting Quiz Bot for deployment...")
    print("📡 API will be available at http://0.0.0.0:5000")
    
    uvicorn.run(
        "deploy:app",
        host="0.0.0.0",
        port=5000,
        reload=False,
        workers=1,
        log_level="info"
    )