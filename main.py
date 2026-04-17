import os
import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from google import genai
from google.genai import errors

logging.basicConfig(level=logging.INFO)

# Инициализация
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()

# Темы: классика кино и юмор
PROMPTS = {
    "Кино": (
        "Придумай интересный вопрос средней сложности про известные фильмы или сериалы, "
        "вышедшие после 2000 года. Вопрос для обычной компании друзей. "
        "Ответ дай СТРОГО в формате JSON: "
        '{"question": "текст", "options": ["1", "2", "3", "4"], "correct_id": 0, "expl": "факт"}'
    ),
    "Юмор": (
        "Придумай забавную логическую загадку или смешной вопрос с подвохом. "
        "Ответ дай СТРОГО в формате JSON: "
        '{"question": "текст", "options": ["1", "2", "3", "4"], "correct_id": 0, "expl": "пояснение"}'
    )
}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🎬 Кино после 2000-х", callback_data="quiz_Кино")
    builder.button(text="🤡 Юморная задача", callback_data="quiz_Юмор")
    builder.adjust(1)
    await message.answer("Выбирай тему и погнали:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("quiz_"))
async def handle_quiz(callback: types.CallbackQuery):
    topic = callback.data.split("_")[1]
    await callback.message.edit_text(f"📡 Ищу крутой вопрос про {topic}...")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=PROMPTS[topic],
            config={'response_mime_type': 'application/json'}
        )
        
        data = json.loads(response.text)
        
        await bot.send_poll(
            chat_id=callback.message.chat.id,
            question=data["question"][:300],
            options=[str(opt)[:100] for opt in data["options"][:10]],
            type='quiz',
            correct_option_id=int(data["correct_id"]),
            explanation=data.get("expl", "Правильный ответ!")[:200],
            is_anonymous=False
        )
        
        # Кнопки для продолжения
        builder = InlineKeyboardBuilder()
        builder.button(text="🎬 Еще кино", callback_data="quiz_Кино")
        builder.button(text="🤡 Еще юмор", callback_data="quiz_Юмор")
        builder.adjust(2)
        await callback.message.answer("Играем дальше?", reply_markup=builder.as_markup())

    except errors.ClientError as e:
        if "429" in str(e):
            await callback.message.answer("🤖 ИИ перегрелся от твоих знаний! Подожди 30 секунд и попробуй снова.")
        else:
            await callback.message.answer("⚠️ Что-то пошло не так. Попробуй еще раз!")
    except Exception as e:
        logging.error(f"Error: {e}")
        await callback.message.answer("⚠️ Ошибка связи. Попробуй нажать кнопку снова.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
