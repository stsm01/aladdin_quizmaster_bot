#!/usr/bin/env python3
"""
Production-ready deployment entry point for Quiz Bot
Handles SSL issues, database connectivity, and graceful error handling
"""

import asyncio
import uvicorn
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

# Настройка продовой базы данных
PRODUCTION_DATABASE_URL = "postgresql://neondb_owner:npg_9BH3JEMRwQna@ep-bitter-lake-a69kivks.us-west-2.aws.neon.tech/neondb?sslmode=require"
os.environ["DATABASE_URL"] = PRODUCTION_DATABASE_URL

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot_deploy.log') if os.path.exists('./') else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)

# Global variables
bot_task: Optional[asyncio.Task] = None
bot_healthy = False

async def start_bot_with_retry():
    """Start the Telegram bot with retry logic"""
    global bot_task, bot_healthy
    
    max_retries = 3
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            logger.info(f"🤖 Starting Telegram bot (attempt {attempt + 1}/{max_retries})...")
            
            # Import here to avoid issues during module loading
            from app.core.config import settings
            from app.bot.bot import main as bot_main
            
            # Check token
            if not settings.bot_token or settings.bot_token == "your_bot_token_here":
                logger.error("❌ Bot token not configured")
                return
            
            # Start bot
            await bot_main()
            bot_healthy = True
            
        except asyncio.CancelledError:
            logger.info("🤖 Bot task cancelled")
            break
        except Exception as e:
            logger.error(f"🤖 Bot error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error("❌ Failed to start bot after all retries")

def check_database_connection():
    """Check database connectivity with error handling"""
    try:
        # Import here to handle connection issues
        from app.core.database import SessionLocal
        
        with SessionLocal() as db:
            # Simple connectivity test
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.warning("⚠️  API will run in degraded mode")
        return False

@asynccontextmanager
async def lifespan(app):
    """Enhanced lifespan manager with error handling"""
    global bot_task
    
    logger.info("🚀 Starting Quiz Bot for production deployment...")
    
    # Check database connectivity
    db_healthy = check_database_connection()
    
    # Start bot only if configured and DB is healthy
    start_bot = False
    try:
        from app.core.config import settings
        if settings.bot_token and settings.bot_token != "your_bot_token_here":
            if db_healthy:
                logger.info("🤖 Starting Telegram bot...")
                bot_task = asyncio.create_task(start_bot_with_retry())
                start_bot = True
            else:
                logger.warning("⚠️  Skipping bot start due to database issues")
        else:
            logger.warning("⚠️  Bot token not configured, running API-only")
    except Exception as e:
        logger.error(f"❌ Error during bot startup: {e}")
    
    if not start_bot:
        logger.info("📡 Running in API-only mode")
    
    yield
    
    # Graceful shutdown
    logger.info("🛑 Shutting down gracefully...")
    if bot_task and not bot_task.done():
        bot_task.cancel()
        try:
            await asyncio.wait_for(bot_task, timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("⚠️  Bot shutdown timeout")
        except asyncio.CancelledError:
            pass
    
    logger.info("✅ Shutdown complete")

# Create FastAPI app
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Telegram Quiz Bot API",
    description="Production deployment of Telegram Quiz Bot",
    version="1.0.0",
    lifespan=lifespan
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Enhanced health check"""
    try:
        # Check database
        db_status = "unknown"
        try:
            from app.core.database import SessionLocal
            with SessionLocal() as db:
                from sqlalchemy import text
                db.execute(text("SELECT 1"))
                db_status = "healthy"
        except Exception:
            db_status = "error"
        
        return {
            "status": "healthy",
            "database": db_status,
            "bot": "running" if (bot_task and not bot_task.done()) else "not_running",
            "bot_healthy": bot_healthy
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "error", "message": str(e)}
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Telegram Quiz Bot API",
        "status": "running",
        "docs": "/docs"
    }

# Include API routes with error handling
try:
    from app.api.routers.public import router as public_router
    from app.api.routers.admin import router as admin_router
    
    app.include_router(public_router, prefix="/public", tags=["public"])
    app.include_router(admin_router, prefix="/admin", tags=["admin"])
    logger.info("✅ API routes loaded successfully")
    
except Exception as e:
    logger.error(f"❌ Error loading API routes: {e}")
    
    # Fallback error endpoint
    @app.get("/error")
    async def error_info():
        return {"error": "API routes failed to load", "details": str(e)}

if __name__ == "__main__":
    logger.info("🚀 Starting production deployment...")
    logger.info("📡 API will be available at http://0.0.0.0:5000")
    
    # Production settings
    uvicorn.run(
        "production_deploy:app",
        host="0.0.0.0",
        port=5000,
        reload=False,
        workers=1,
        log_level="info",
        access_log=True,
        timeout_keep_alive=65,
        timeout_graceful_shutdown=30
    )