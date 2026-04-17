import os
import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from google import genai

logging.basicConfig(level=logging.INFO)

# Инициализация нового клиента Google AI
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()

PROMPT = (
    "Ты ведущий квиза. Придумай 1 вопрос на тему {topic}. "
    "Ответ дай СТРОГО в формате JSON: "
    '{{"question": "текст", "options": ["вар1", "вар2", "вар3", "вар4"], "correct_id": 0, "expl": "факт"}}'
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Stranger Things 🧇", callback_data="t_Stranger Things")
    builder.button(text="Кино 🍿", callback_data="t_Movies")
    builder.button(text="Бизнес 🕯", callback_data="t_Business")
    builder.button(text="Случайный факт 🎲", callback_data="t_General")
    builder.adjust(2)
    await message.answer("Выбери тему квиза:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("t_"))
async def handle_quiz(callback: types.CallbackQuery):
    topic = callback.data.split("_")[1]
    await callback.message.answer(f"⏳ Генерирую вопрос: {topic}...")
    try:
        # Новый способ вызова Gemini
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=PROMPT.format(topic=topic)
        )
        
        # Умная очистка JSON
        raw_text = response.text
        start = raw_text.find('{')
        end = raw_text.rfind('}') + 1
        data = json.loads(raw_text[start:end])
        
        await bot.send_poll(
            chat_id=callback.message.chat.id,
            question=data["question"][:300],
            options=[str(opt)[:100] for opt in data["options"][:10]],
            type='quiz',
            correct_option_id=int(data["correct_id"]),
            explanation=data.get("expl", "Интересно!")[:200],
            is_anonymous=False
        )
    except Exception as e:
        logging.error(f"AI Error: {e}")
        await callback.message.answer("Связь с Демогоргоном прервана... Попробуй еще раз!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
