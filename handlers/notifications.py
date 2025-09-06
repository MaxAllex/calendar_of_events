import asyncio
import logging
from datetime import datetime, timedelta
from typing import List
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from db.database import Database

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, bot: Bot, db: Database):
        self.bot = bot
        self.db = db
        self.running = False
    
    async def start_notification_service(self):
        """Запуск сервиса уведомлений"""
        self.running = True
        logger.info("Notification service started")
        
        while self.running:
            try:
                await self.check_and_send_notifications()
                await asyncio.sleep(60)  # Проверяем каждую минуту
            except Exception as e:
                logger.error(f"Error in notification service: {e}")
                await asyncio.sleep(60)
    
    async def stop_notification_service(self):
        """Остановка сервиса уведомлений"""
        self.running = False
        logger.info("Notification service stopped")
    
    async def check_and_send_notifications(self):
        """Проверка и отправка уведомлений о предстоящих событиях"""
        try:
            # Получаем события, которые начнутся в ближайшие 2 часа
            upcoming_events = self.db.get_upcoming_events(hours_ahead=2)
            
            for event in upcoming_events:
                event_id, title, description, event_date, created_by = event
                event_datetime = datetime.fromisoformat(event_date)
                time_until_event = event_datetime - datetime.now()
                
                # Отправляем уведомления за 1 час и за 15 минут
                if self._should_send_notification(time_until_event):
                    await self._send_event_notification(event)
                    self.db.mark_notification_sent(event_id)
                    
        except Exception as e:
            logger.error(f"Error checking notifications: {e}")
    
    def _should_send_notification(self, time_until_event: timedelta) -> bool:
        """Определяет, нужно ли отправить уведомление"""
        total_minutes = time_until_event.total_seconds() / 60
        
        # Уведомляем за 60 минут или за 15 минут
        return abs(total_minutes - 60) < 2 or abs(total_minutes - 15) < 2
    
    async def _send_event_notification(self, event: tuple):
        """Отправка уведомления о событии"""
        try:
            event_id, title, description, event_date, created_by = event
            event_datetime = datetime.fromisoformat(event_date)
            time_until_event = event_datetime - datetime.now()
            
            # Определяем время до события
            if time_until_event.total_seconds() / 60 < 20:
                time_text = "15 минут"
            else:
                time_text = "1 час"
            
            # Создаем клавиатуру с кнопкой "Посмотреть события"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📅 Посмотреть все события", callback_data="show_events")]
            ])
            
            notification_text = (
                f"🔔 Напоминание о событии!\n\n"
                f"📝 {title}\n"
                f"📅 {event_datetime.strftime('%d.%m.%Y %H:%M')}\n"
                f"⏰ До события осталось: {time_text}\n\n"
                f"ID события: {event_id}"
            )
            
            # Отправляем уведомление создателю события
            await self.bot.send_message(
                chat_id=created_by,
                text=notification_text,
                reply_markup=keyboard
            )
            
            logger.info(f"Notification sent for event {event_id} to user {created_by}")
            
        except Exception as e:
            logger.error(f"Error sending notification for event {event[0]}: {e}")
    
    async def send_manual_notification(self, chat_id: int, message: str):
        """Отправка ручного уведомления"""
        try:
            await self.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            logger.error(f"Error sending manual notification: {e}")


# Глобальная переменная для сервиса уведомлений
notification_service = None


async def start_notifications(bot: Bot, db: Database):
    """Запуск сервиса уведомлений"""
    global notification_service
    notification_service = NotificationService(bot, db)
    await notification_service.start_notification_service()


async def stop_notifications():
    """Остановка сервиса уведомлений"""
    global notification_service
    if notification_service:
        await notification_service.stop_notification_service()
