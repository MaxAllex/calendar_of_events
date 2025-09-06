import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = "calendar.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    event_date TEXT NOT NULL,
                    created_by INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    notification_sent BOOLEAN DEFAULT FALSE
                )
            """)
            conn.commit()
            logger.info("Database initialized successfully")
    
    def add_event(self, title: str, description: str, event_date: str, user_id: int) -> int:
        """Добавить событие в календарь"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO events (title, description, event_date, created_by, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (title, description, event_date, user_id, datetime.now().isoformat()))
            conn.commit()
            return cursor.lastrowid
    
    def get_events(self, limit: int = 10) -> List[Tuple]:
        """Получить список событий"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, description, event_date, created_by, created_at
                FROM events
                WHERE event_date >= date('now')
                ORDER BY event_date ASC
                LIMIT ?
            """, (limit,))
            return cursor.fetchall()
    
    def get_event_by_id(self, event_id: int) -> Optional[Tuple]:
        """Получить событие по ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, description, event_date, created_by, created_at
                FROM events
                WHERE id = ?
            """, (event_id,))
            return cursor.fetchone()
    
    def delete_event(self, event_id: int, user_id: int) -> bool:
        """Удалить событие (только создатель может удалить)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM events
                WHERE id = ? AND created_by = ?
            """, (event_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_upcoming_events(self, hours_ahead: int = 24) -> List[Tuple]:
        """Получить события, которые начнутся в ближайшие часы"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            future_time = (datetime.now() + timedelta(hours=hours_ahead)).isoformat()
            cursor.execute("""
                SELECT id, title, description, event_date, created_by
                FROM events
                WHERE event_date BETWEEN datetime('now') AND ?
                AND notification_sent = FALSE
                ORDER BY event_date ASC
            """, (future_time,))
            return cursor.fetchall()
    
    def mark_notification_sent(self, event_id: int):
        """Отметить, что уведомление о событии отправлено"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE events
                SET notification_sent = TRUE
                WHERE id = ?
            """, (event_id,))
            conn.commit()
    
    def get_events_by_user(self, user_id: int) -> List[Tuple]:
        """Получить события, созданные пользователем"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, description, event_date, created_at
                FROM events
                WHERE created_by = ?
                ORDER BY event_date ASC
            """, (user_id,))
            return cursor.fetchall()
