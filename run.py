#!/usr/bin/env python3
"""
Точка входа для запуска календарного бота
"""

from main.bot import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
