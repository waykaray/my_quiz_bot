import os
import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from google import genai

logging.basicConfig(level=logging.INFO)

# Инициализация клиентов
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()

# Промпт под две задачи
PROMPT = (
    "Ты ведущий квиза. Тема: {topic}. "
    "Если тема 'Кино', придумай вопрос средней сложности про фильмы или сериалы после 2000 года. "
    "Если тема 'Юмор', придумай смешную логическую задачку или вопрос с подвохом. "
    "Ответ дай СТРОГО в формате JSON: "
    '{{"question": "текст", "options": ["1", "2", "3", "4"], "correct_id": 0, "expl": "пояснение"}}'
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🎬 Кино (после 2000-х)", callback_data="t_Кино")
    builder.button(text="🤡 Юморные задачи", callback_data="t_Юмор")
    builder.adjust(1)
    await message.answer("Выбирай режим игры:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("t_"))
async def handle_quiz(callback: types.CallbackQuery):
    topic = callback.data.split("_")[1]
    await callback.message.edit_text(f"⏳ Генерирую вопрос: {topic}...")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=PROMPT.format(topic=topic),
            config={'response_mime_type': 'application/json'}
        )
        
        # Безопасная загрузка JSON
        data = json.loads(response.text.strip())
        
        await bot.send_poll(
            chat_id=callback.message.chat.id,
            question=data["question"][:300],
            options=[str(opt)[:100] for opt in data["options"][:10]],
            type='quiz',
            correct_option_id=int(data["correct_id"]),
            explanation=data.get("expl", "Правильно!")[:200],
            is_anonymous=False
        )
        
        await asyncio.sleep(1)
        await callback.message.answer("Продолжим?", reply_markup=get_retry_keyboard())
        
    except Exception as e:
        logging.error(f"Error: {e}")
        await callback.message.answer("⚠️ Ошибка связи. Попробуй еще раз через 5 секунд!")

def get_retry_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🎬 Кино", callback_data="t_Кино")
    builder.button(text="🤡 Юмор", callback_data="t_Юмор")
    builder.adjust(2)
    return builder.as_markup()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
