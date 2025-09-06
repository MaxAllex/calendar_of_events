import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from handlers.commands import router as commands_router
from handlers.notifications import start_notifications, stop_notifications
from db.database import Database

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CalendarBot:
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("BOT_TOKEN не найден в переменных окружения!")
        
        self.bot = Bot(token=self.bot_token)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.db = Database()
        
        # Регистрируем роутеры
        self.dp.include_router(commands_router)
    
    async def start(self):
        """Запуск бота"""
        try:
            logger.info("Starting calendar bot...")
            
            # Запускаем сервис уведомлений в фоне
            notification_task = asyncio.create_task(
                start_notifications(self.bot, self.db)
            )
            
            # Запускаем бота
            await self.dp.start_polling(self.bot)
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Остановка бота"""
        try:
            logger.info("Stopping calendar bot...")
            await stop_notifications()
            await self.bot.session.close()
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")


async def main():
    """Главная функция"""
    try:
        bot = CalendarBot()
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
