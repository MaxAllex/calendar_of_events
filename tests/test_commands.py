import pytest
from datetime import datetime, timedelta
from handlers.commands import parse_date


class TestParseDate:
    def test_parse_standard_formats(self):
        """Тест парсинга стандартных форматов даты"""
        # Тест формата YYYY-MM-DD HH:MM
        result = parse_date("2024-01-15 15:30")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 15
        assert result.minute == 30
        
        # Тест формата YYYY-MM-DD
        result = parse_date("2024-01-15")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 0
        assert result.minute == 0
    
    def test_parse_special_cases(self):
        """Тест парсинга специальных случаев"""
        # Тест "today"
        result = parse_date("today")
        assert result is not None
        now = datetime.now()
        assert result.date() == now.date()
        assert result.hour == 12
        assert result.minute == 0
        
        # Тест "tomorrow"
        result = parse_date("tomorrow")
        assert result is not None
        tomorrow = datetime.now() + timedelta(days=1)
        assert result.date() == tomorrow.date()
        assert result.hour == 12
        assert result.minute == 0
        
        # Тест "+N days"
        result = parse_date("+3")
        assert result is not None
        future_date = datetime.now() + timedelta(days=3)
        assert result.date() == future_date.date()
        assert result.hour == 12
        assert result.minute == 0
    
    def test_parse_invalid_formats(self):
        """Тест парсинга неверных форматов"""
        # Неверные форматы должны возвращать None
        assert parse_date("invalid-date") is None
        assert parse_date("32-13-2024") is None
        assert parse_date("2024-13-32") is None
        assert parse_date("") is None
        assert parse_date("+abc") is None
    
    def test_parse_case_insensitive(self):
        """Тест нечувствительности к регистру"""
        result1 = parse_date("TODAY")
        result2 = parse_date("today")
        result3 = parse_date("Today")
        
        assert result1 is not None
        assert result2 is not None
        assert result3 is not None
        
        # Все должны быть в один день
        assert result1.date() == result2.date() == result3.date()
    
    def test_parse_edge_cases(self):
        """Тест граничных случаев"""
        # Тест високосного года
        result = parse_date("2024-02-29")
        assert result is not None
        assert result.year == 2024
        assert result.month == 2
        assert result.day == 29
        
        # Тест конца года
        result = parse_date("2024-12-31 23:59")
        assert result is not None
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 31
        assert result.hour == 23
        assert result.minute == 59
