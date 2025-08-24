#!/usr/bin/env python3
"""
Standalone script to run only the Telegram bot
"""

import asyncio
from app.bot.bot import main

if __name__ == "__main__":
    print("🤖 Starting Telegram Quiz Bot...")
    asyncio.run(main())
