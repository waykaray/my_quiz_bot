import os
import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from google import genai

# Логирование для Render
logging.basicConfig(level=logging.INFO)

# Клиенты (Ключи берем из Environment Variables)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()

# Мощный промпт 2026 года
PROMPT = (
    "Ты — ироничный ведущий квиза. Тема: {topic}. "
    "Если тема 'Кино', опиши известный фильм или сериал как абсурдное ТЗ от заказчика или странную жалобу. "
    "Если тема 'Юмор', придумай смешную логическую задачку-парадокс с подвохом. "
    "Ответ дай СТРОГО в формате JSON: "
    '{{"question": "текст", "options": ["1", "2", "3", "4"], "correct_id": 0, "expl": "пояснение"}}'
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🎬 Угадай фильм (Кино-ТЗ)", callback_data="t_Кино")
    builder.button(text="🤡 Юморные задачки", callback_data="t_Юмор")
    builder.adjust(1)
    
    await message.answer(
        "Добро пожаловать в ИИ-Квиз 2026! 🚀\nВыбери режим игры:", 
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("t_"))
async def handle_quiz(callback: types.CallbackQuery):
    topic = callback.data.split("_")[1]
    # Редактируем старое сообщение, чтобы не плодить текст
    await callback.message.edit_text(f"📡 Опрашиваю нейросеть по теме: {topic}...")
    
    try:
        # Используем Gemini 2.0 Flash с принудительным JSON-форматом
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=PROMPT.format(topic=topic),
            config={'response_mime_type': 'application/json'}
        )
        
        # В 2026-м Gemini в JSON-режиме возвращает чистый объект
        data = json.loads(response.text)
        
        await bot.send_poll(
            chat_id=callback.message.chat.id,
            question=data["question"][:300],
            options=[str(opt)[:100] for opt in data["options"][:10]],
            type='quiz',
            correct_option_id=int(data["correct_id"]),
            explanation=data.get("expl", "Вот так вот!")[:200],
            is_anonymous=False
        )
        
        # Возвращаем меню выбора после паузы
        await asyncio.sleep(1)
        await callback.message.answer("Играем дальше?", reply_markup=callback.message.reply_markup)
        
    except Exception as e:
        logging.error(f"Error: {e}")
        await callback.message.answer("⚠️ Ошибка матрицы. Попробуй еще раз через 5 секунд.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
