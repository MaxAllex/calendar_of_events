import pytest
import tempfile
import os
from datetime import datetime, timedelta
from db.database import Database


@pytest.fixture
def temp_db():
    """Создает временную базу данных для тестов"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    db = Database(db_path)
    yield db
    
    # Очистка после тестов
    os.unlink(db_path)


class TestDatabase:
    def test_init_database(self, temp_db):
        """Тест инициализации базы данных"""
        # Проверяем, что таблица events создана
        with temp_db.db_path as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
            result = cursor.fetchone()
            assert result is not None
    
    def test_add_event(self, temp_db):
        """Тест добавления события"""
        event_id = temp_db.add_event(
            title="Тестовое событие",
            description="Описание тестового события",
            event_date="2024-01-15 15:00",
            user_id=12345
        )
        
        assert event_id is not None
        assert isinstance(event_id, int)
        
        # Проверяем, что событие действительно добавлено
        event = temp_db.get_event_by_id(event_id)
        assert event is not None
        assert event[1] == "Тестовое событие"  # title
        assert event[2] == "Описание тестового события"  # description
        assert event[4] == 12345  # created_by
    
    def test_get_events(self, temp_db):
        """Тест получения списка событий"""
        # Добавляем несколько событий
        temp_db.add_event("Событие 1", "Описание 1", "2024-12-31 12:00", 12345)
        temp_db.add_event("Событие 2", "Описание 2", "2024-12-31 13:00", 12346)
        
        events = temp_db.get_events(limit=5)
        assert len(events) == 2
        assert events[0][1] == "Событие 1"
        assert events[1][1] == "Событие 2"
    
    def test_get_event_by_id(self, temp_db):
        """Тест получения события по ID"""
        event_id = temp_db.add_event(
            "Тестовое событие",
            "Описание",
            "2024-01-15 15:00",
            12345
        )
        
        event = temp_db.get_event_by_id(event_id)
        assert event is not None
        assert event[0] == event_id
        
        # Тест несуществующего события
        non_existent = temp_db.get_event_by_id(99999)
        assert non_existent is None
    
    def test_delete_event(self, temp_db):
        """Тест удаления события"""
        event_id = temp_db.add_event(
            "Событие для удаления",
            "Описание",
            "2024-01-15 15:00",
            12345
        )
        
        # Удаляем событие
        success = temp_db.delete_event(event_id, 12345)
        assert success is True
        
        # Проверяем, что событие удалено
        event = temp_db.get_event_by_id(event_id)
        assert event is None
        
        # Тест удаления чужого события
        event_id2 = temp_db.add_event(
            "Чужое событие",
            "Описание",
            "2024-01-15 15:00",
            12346
        )
        
        success = temp_db.delete_event(event_id2, 12345)  # Пытаемся удалить чужое событие
        assert success is False
    
    def test_get_events_by_user(self, temp_db):
        """Тест получения событий пользователя"""
        # Добавляем события от разных пользователей
        temp_db.add_event("Событие 1", "Описание", "2024-01-15 15:00", 12345)
        temp_db.add_event("Событие 2", "Описание", "2024-01-16 15:00", 12345)
        temp_db.add_event("Событие 3", "Описание", "2024-01-17 15:00", 12346)
        
        user_events = temp_db.get_events_by_user(12345)
        assert len(user_events) == 2
        assert user_events[0][1] == "Событие 1"
        assert user_events[1][1] == "Событие 2"
    
    def test_get_upcoming_events(self, temp_db):
        """Тест получения предстоящих событий"""
        now = datetime.now()
        future_time = now + timedelta(hours=1)
        
        # Добавляем событие в будущем
        event_id = temp_db.add_event(
            "Будущее событие",
            "Описание",
            future_time.isoformat(),
            12345
        )
        
        upcoming = temp_db.get_upcoming_events(hours_ahead=2)
        assert len(upcoming) == 1
        assert upcoming[0][0] == event_id
    
    def test_mark_notification_sent(self, temp_db):
        """Тест отметки уведомления как отправленного"""
        event_id = temp_db.add_event(
            "Событие",
            "Описание",
            "2024-01-15 15:00",
            12345
        )
        
        # Отмечаем уведомление как отправленное
        temp_db.mark_notification_sent(event_id)
        
        # Проверяем в базе данных
        with temp_db.db_path as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT notification_sent FROM events WHERE id = ?", (event_id,))
            result = cursor.fetchone()
            assert result[0] is True
