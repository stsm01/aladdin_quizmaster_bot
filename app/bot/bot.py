"""Main Telegram bot module"""

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from ..core.config import settings
from .handlers import register_handlers
from .storage import PostgreSQLStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

async def main():
    """Main bot function"""
    # Check bot token
    if not settings.bot_token or settings.bot_token == "your_bot_token_here":
        logger.error("Bot token is not configured. Please set BOT_TOKEN environment variable.")
        return
    
    # Initialize bot and dispatcher with persistent storage
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Initialize persistent storage
    storage = PostgreSQLStorage()
    dp = Dispatcher(storage=storage)
    
    # Register handlers
    register_handlers(dp)
    
    logger.info("🤖 Starting Telegram bot...")
    
    try:
        # Start polling
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise  # Re-raise to allow retry logic to work
    finally:
        try:
            await bot.session.close()
            await storage.close()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
            pass

if __name__ == "__main__":
    asyncio.run(main())
