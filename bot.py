#!/usr/bin/env python3
"""
Telegram Bot для Telegram Mini App с системой аутентификации
"""

import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токен бота из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEB_APP_URL = os.getenv("WEB_APP_URL", "http://localhost:8000")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения. Создайте файл .env с токеном бота.")

# Создаем экземпляры бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    """
    Обработчик команды /start
    Отправляет приветственное сообщение с кнопкой для открытия Mini App
    """
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # Проверяем, является ли пользователь администратором
    admin_user_id = os.getenv("ADMIN_USER_ID", "").strip()
    is_admin = str(user_id) == admin_user_id
    
    welcome_text = f"👋 Привет, {username}!\n\n"
    welcome_text += "🍰 Добро пожаловать в пекарню 'Свежая выпечка'!\n\n"
    
    if is_admin:
        welcome_text += "👑 Вы вошли как администратор.\n"
        welcome_text += "У вас есть доступ к панели управления товарами.\n\n"
    else:
        welcome_text += "📱 Здесь вы можете:\n"
        welcome_text += "• Просматривать наше меню\n"
        welcome_text += "• Делать заказы\n"
        welcome_text += "• Узнавать о доставке\n\n"
    
    welcome_text += "Нажмите кнопку ниже, чтобы открыть приложение:"
    
    # Создаем кнопку для открытия Mini App
    web_app_button = types.InlineKeyboardButton(
        text="🍰 Открыть пекарню" if not is_admin else "👑 Открыть админ-панель",
        web_app=types.WebAppInfo(url=WEB_APP_URL)
    )
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[web_app_button]])
    
    await message.answer(
        welcome_text,
        reply_markup=keyboard
    )
    
    logger.info(f"Пользователь {user_id} ({username}) {'админ' if is_admin else 'обычный'} открыл бота")

@dp.message(Command("help"))
async def help_command(message: types.Message):
    """
    Обработчик команды /help
    Показывает справку по использованию бота
    """
    help_text = """
🤖 <b>Справка по боту пекарни</b>

<b>Доступные команды:</b>
/start - Начать работу с ботом
/help - Показать эту справку
/menu - Открыть меню пекарни
/admin - Информация для администраторов

<b>Как пользоваться:</b>
1. Нажмите /start для начала
2. Нажмите кнопку "Открыть пекарню"
3. Выберите товары и оформите заказ

<b>Поддержка:</b>
Если у вас есть вопросы, обратитесь к администратору.
    """
    
    await message.answer(help_text, parse_mode="HTML")

@dp.message(Command("menu"))
async def menu_command(message: types.Message):
    """
    Обработчик команды /menu
    Отправляет кнопку для открытия меню
    """
    menu_text = "🍰 <b>Наше меню</b>\n\n"
    menu_text += "• Булочка с корицей - 150₽\n"
    menu_text += "• Круассан с шоколадом - 200₽\n"
    menu_text += "• Пончик с глазурью - 120₽\n"
    menu_text += "• Пирожное Наполеон - 300₽\n"
    menu_text += "• Торт Чизкейк - 450₽\n\n"
    menu_text += "Нажмите кнопку ниже, чтобы открыть полное меню и сделать заказ:"
    
    web_app_button = types.InlineKeyboardButton(
        text="🍰 Открыть меню",
        web_app=types.WebAppInfo(url=WEB_APP_URL)
    )
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[web_app_button]])
    
    await message.answer(menu_text, reply_markup=keyboard, parse_mode="HTML")

@dp.message(Command("admin"))
async def admin_command(message: types.Message):
    """
    Обработчик команды /admin
    Показывает информацию для администраторов
    """
    user_id = message.from_user.id
    admin_user_id = os.getenv("ADMIN_USER_ID", "").strip()
    
    if str(user_id) == admin_user_id:
        admin_text = "👑 <b>Панель администратора</b>\n\n"
        admin_text += "У вас есть доступ к следующим функциям:\n"
        admin_text += "• Добавление новых товаров\n"
        admin_text += "• Редактирование существующих товаров\n"
        admin_text += "• Удаление товаров\n"
        admin_text += "• Просмотр всех заказов\n"
        admin_text += "• Загрузка изображений\n\n"
        admin_text += "Нажмите кнопку ниже, чтобы открыть админ-панель:"
        
        web_app_button = types.InlineKeyboardButton(
            text="👑 Открыть админ-панель",
            web_app=types.WebAppInfo(url=WEB_APP_URL)
        )
        
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[web_app_button]])
        
        await message.answer(admin_text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(
            "❌ У вас нет прав администратора.\n"
            "Обратитесь к администратору для получения доступа.",
            parse_mode="HTML"
        )

@dp.message()
async def handle_other_messages(message: types.Message):
    """
    Обработчик всех остальных сообщений
    """
    await message.answer(
        "🤖 Я не понимаю эту команду.\n"
        "Используйте /help для получения справки или /start для начала работы."
    )

async def main():
    """
    Основная функция для запуска бота
    """
    logger.info("🚀 Запуск Telegram бота...")
    logger.info(f"🌐 Web App URL: {WEB_APP_URL}")
    
    try:
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот @{bot_info.username} запущен успешно")
        
        # Запускаем polling
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
        raise
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
