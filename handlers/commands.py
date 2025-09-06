import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db.database import Database

logger = logging.getLogger(__name__)
router = Router()
db = Database()


class AddEventStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_description = State()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    await message.answer(
        "📅 Добро пожаловать в календарь событий!\n\n"
        "Доступные команды:\n"
        "/addevent - добавить событие\n"
        "/events - показать ближайшие события\n"
        "/myevents - показать мои события\n"
        "/deleteevent - удалить событие\n"
        "/help - помощь"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = """
📅 Календарь событий - Справка

🔹 /addevent - добавить новое событие
   Формат: /addevent [дата] [описание]
   Пример: /addevent 2024-01-15 15:00 Встреча с командой

🔹 /events - показать ближайшие события (до 10)

🔹 /myevents - показать мои события

🔹 /deleteevent [id] - удалить событие по ID
   Пример: /deleteevent 5

🔹 /help - показать эту справку

📝 Форматы даты:
• YYYY-MM-DD HH:MM (2024-01-15 15:00)
• YYYY-MM-DD (2024-01-15)
• today, tomorrow
• +N days (через N дней)
    """
    await message.answer(help_text)


@router.message(Command("addevent"))
async def cmd_addevent(message: Message, state: FSMContext):
    """Обработчик команды /addevent"""
    args = message.text.split()[1:]  # Убираем команду
    
    if len(args) < 2:
        await message.answer(
            "❌ Неверный формат команды!\n\n"
            "Используйте: /addevent [дата] [описание]\n"
            "Пример: /addevent 2024-01-15 15:00 Встреча с командой"
        )
        return
    
    # Парсим дату и описание
    try:
        date_str = args[0]
        description = " ".join(args[1:])
        
        # Парсим дату
        event_date = parse_date(date_str)
        if not event_date:
            await message.answer("❌ Неверный формат даты!")
            return
        
        # Добавляем событие
        event_id = db.add_event(
            title=description[:50],  # Ограничиваем длину заголовка
            description=description,
            event_date=event_date.isoformat(),
            user_id=message.from_user.id
        )
        
        await message.answer(
            f"✅ Событие добавлено!\n\n"
            f"📅 Дата: {event_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"📝 Описание: {description}\n"
            f"🆔 ID: {event_id}"
        )
        
    except Exception as e:
        logger.error(f"Error adding event: {e}")
        await message.answer("❌ Произошла ошибка при добавлении события")


@router.message(Command("events"))
async def cmd_events(message: Message):
    """Обработчик команды /events"""
    try:
        events = db.get_events(limit=10)
        
        if not events:
            await message.answer("📅 Нет предстоящих событий")
            return
        
        response = "📅 Ближайшие события:\n\n"
        
        for event in events:
            event_id, title, description, event_date, created_by, created_at = event
            event_datetime = datetime.fromisoformat(event_date)
            
            response += (
                f"🆔 {event_id}\n"
                f"📅 {event_datetime.strftime('%d.%m.%Y %H:%M')}\n"
                f"📝 {title}\n"
                f"👤 Создал: {created_by}\n\n"
            )
        
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        await message.answer("❌ Произошла ошибка при получении событий")


@router.message(Command("myevents"))
async def cmd_myevents(message: Message):
    """Обработчик команды /myevents"""
    try:
        events = db.get_events_by_user(message.from_user.id)
        
        if not events:
            await message.answer("📅 У вас нет созданных событий")
            return
        
        response = "📅 Ваши события:\n\n"
        
        for event in events:
            event_id, title, description, event_date, created_at = event
            event_datetime = datetime.fromisoformat(event_date)
            
            response += (
                f"🆔 {event_id}\n"
                f"📅 {event_datetime.strftime('%d.%m.%Y %H:%M')}\n"
                f"📝 {title}\n\n"
            )
        
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Error getting user events: {e}")
        await message.answer("❌ Произошла ошибка при получении ваших событий")


@router.message(Command("deleteevent"))
async def cmd_deleteevent(message: Message):
    """Обработчик команды /deleteevent"""
    args = message.text.split()[1:]
    
    if len(args) != 1:
        await message.answer(
            "❌ Неверный формат команды!\n\n"
            "Используйте: /deleteevent [id]\n"
            "Пример: /deleteevent 5"
        )
        return
    
    try:
        event_id = int(args[0])
        
        # Проверяем, существует ли событие
        event = db.get_event_by_id(event_id)
        if not event:
            await message.answer("❌ Событие с таким ID не найдено")
            return
        
        # Удаляем событие
        success = db.delete_event(event_id, message.from_user.id)
        
        if success:
            await message.answer(f"✅ Событие {event_id} удалено")
        else:
            await message.answer("❌ Вы можете удалять только свои события")
            
    except ValueError:
        await message.answer("❌ ID события должен быть числом")
    except Exception as e:
        logger.error(f"Error deleting event: {e}")
        await message.answer("❌ Произошла ошибка при удалении события")


def parse_date(date_str: str) -> datetime:
    """Парсинг даты из различных форматов"""
    date_str = date_str.lower().strip()
    
    try:
        # Стандартные форматы
        if " " in date_str:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        else:
            return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        pass
    
    # Специальные случаи
    now = datetime.now()
    
    if date_str == "today":
        return now.replace(hour=12, minute=0, second=0, microsecond=0)
    elif date_str == "tomorrow":
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=12, minute=0, second=0, microsecond=0)
    elif date_str.startswith("+"):
        try:
            days = int(date_str[1:])
            future_date = now + timedelta(days=days)
            return future_date.replace(hour=12, minute=0, second=0, microsecond=0)
        except ValueError:
            pass
    
    return None
