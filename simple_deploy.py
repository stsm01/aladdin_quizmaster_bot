#!/usr/bin/env python3
"""
Simple deployment entry point - API only
Use this if bot integration causes issues
"""

import uvicorn
import logging
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("🚀 Starting Quiz Bot API (Simple Deploy)")
    logger.info("📡 API will be available at http://0.0.0.0:5000")
    logger.info("⚠️  Bot is NOT running in this mode")
    
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=5000,
        reload=False,
        workers=1,
        log_level="info"
    )