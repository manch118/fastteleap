#!/usr/bin/env python3
"""
Скрипт для запуска FastAPI сервера и Telegram бота одновременно
"""

import asyncio
import subprocess
import sys
import os
import signal
import time
from pathlib import Path

# Add project root to the Python path to resolve imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def check_env_file():
    """Проверяет наличие и корректность .env файла"""
    env_path = Path(".env")
    
    if not env_path.exists():
        print("❌ Файл .env не найден!")
        print("📋 Создайте файл .env на основе env_example.txt:")
        print("   cp env_example.txt .env")
        print("   Затем заполните переменные BOT_TOKEN и ADMIN_USER_ID")
        return False
    
    # Проверяем содержимое .env
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if "your_telegram_bot_token_here" in content:
        print("❌ BOT_TOKEN не настроен в .env файле!")
        print("📋 Получите токен у @BotFather и укажите его в .env")
        return False
        
    if "123456789" in content:
        print("❌ ADMIN_USER_ID не настроен в .env файле!")
        print("📋 Получите ваш ID у @userinfobot и укажите его в .env")
        return False
    
    print("OK: Файл .env настроен корректно")
    return True

def start_fastapi_server():
    """Запускает FastAPI сервер"""
    print("🚀 Запуск FastAPI сервера...")
    try:
        # Используем uvicorn для запуска сервера
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ])
        return process
    except Exception as e:
        print(f"❌ Ошибка запуска FastAPI сервера: {e}")
        return None

def start_telegram_bot():
    """Запускает Telegram бота"""
    print("🤖 Запуск Telegram бота...")
    try:
        process = subprocess.Popen([sys.executable, "bot.py"])
        return process
    except Exception as e:
        print(f"❌ Ошибка запуска Telegram бота: {e}")
        return None

def main():
    """Основная функция"""
    print("Запуск Telegram Mini App с аутентификацией")
    print("=" * 50)
    
    # Проверяем .env файл
    if not check_env_file():
        return 1
    
    # Запускаем FastAPI сервер
    fastapi_process = start_fastapi_server()
    if not fastapi_process:
        return 1
    
    # Ждем немного, чтобы сервер запустился
    time.sleep(3)
    
    # Запускаем Telegram бота
    bot_process = start_telegram_bot()
    if not bot_process:
        fastapi_process.terminate()
        return 1
    
    print("\n✅ Оба сервиса запущены успешно!")
    print("🌐 FastAPI сервер: http://localhost:8000")
    print("📱 Telegram бот: готов к работе")
    print("📚 API документация: http://localhost:8000/docs")
    print("\n🛑 Для остановки нажмите Ctrl+C")
    
    try:
        # Ждем завершения процессов
        while True:
            if fastapi_process.poll() is not None:
                print("❌ FastAPI сервер остановлен")
                break
            if bot_process.poll() is not None:
                print("❌ Telegram бот остановлен")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Остановка сервисов...")
        
        # Останавливаем процессы
        if fastapi_process:
            fastapi_process.terminate()
        if bot_process:
            bot_process.terminate()
        
        print("✅ Сервисы остановлены")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
