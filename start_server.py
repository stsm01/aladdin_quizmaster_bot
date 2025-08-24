#!/usr/bin/env python3
"""
Simple server startup script for deployment.
Starts only the FastAPI server on port 5000.
"""

import os
import uvicorn

def main():
    """Start the FastAPI server for deployment"""
    print("🚀 Starting Quiz Bot API Server...")
    
    # Set environment variables for deployment
    os.environ.setdefault("API_HOST", "0.0.0.0")
    os.environ.setdefault("API_PORT", "5000")
    
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=5000,
        reload=False,
        access_log=True
    )

if __name__ == "__main__":
    main()