#!/usr/bin/env python3
"""
Simplified deployment entry point for Quiz Bot API
Optimized for Replit deployment environment
"""

import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Quiz Bot API for deployment...")
    
    # Direct uvicorn configuration for deployment
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0", 
        port=5000,
        reload=False,
        workers=1,
        log_level="info"
    )