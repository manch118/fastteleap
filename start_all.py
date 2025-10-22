#!/usr/bin/env python3
"""
Скрипт для запуска FastAPI сервера и Telegram бота одновременно
"""

import subprocess
import sys
import os
import time
from pathlib import Path


def ensure_env_file():
    """Создаёт .env файл, если его нет, используя реальные ENV из Render"""
    env_path = Path(".env")

    if not env_path.exists():
        print("⚙️ Файл .env не найден — создаю новый из системных переменных Render...")

        # Список нужных переменных
        env_vars = [
            "BOT_TOKEN",
            "ADMIN_USER_ID",
            "WEB_APP_URL",
            "YOOKASSA_SHOP_ID",
            "YOOKASSA_SECRET_KEY"
        ]

        with open(env_path, "w", encoding="utf-8") as f:
            for var in env_vars:
                value = os.getenv(var, "")
                f.write(f"{var}={value}\n")

        print("✅ Файл .env успешно создан и заполнен из Render Environment Variables.")
    else:
        print("✅ Файл .env найден.")


def check_env_file():
    """Проверяет корректность .env файла"""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ Файл .env не найден!")
        return False

    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()

    if "BOT_TOKEN=" not in content or "ADMIN_USER_ID=" not in content:
        print("❌ В .env отсутствуют нужные переменные!")
        return False

    print("OK: .env файл корректен")
    return True


def start_fastapi_server():
    """Запускает FastAPI сервер"""
    print("🚀 Запуск FastAPI сервера...")
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "main:app",
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
    print("Запуск Telegram Mini App с аутентификацией")
    print("=" * 50)

    # Создаём .env из Render ENV
    ensure_env_file()

    # Проверяем .env
    if not check_env_file():
        return 1

    # Запускаем FastAPI
    fastapi_process = start_fastapi_server()
    if not fastapi_process:
        return 1

    # Даем серверу стартовать
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
        if fastapi_process:
            fastapi_process.terminate()
        if bot_process:
            bot_process.terminate()
        print("✅ Сервисы остановлены")

    return 0


if __name__ == "__main__":
    sys.exit(main())