import os 
import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import google.generativeai as genai

TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

bot = Bot(token=TOKEN)
dp = Dispatcher()

PROMPT = (
    "Сгенерируй сложный вопрос для квиза на тему {topic}. "
    "Ответ дай СТРОГО в формате JSON: "
    '{{"question": "текст", "options": ["вар1", "вар2", "вар3", "вар4"], "correct_id": 0}}'
)

@dp.message(Command("quiz"))
async def send_quiz(message: types.Message):
    topic = message.text.replace("/quiz", "").strip() or "Общие знания"
    try:
        response = model.generate_content(PROMPT.format(topic=topic))
        # Очищаем ответ от лишних символов, если они будут
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        
        await bot.send_poll(
            chat_id=message.chat.id,
            question=data["question"],
            options=data["options"],
            type='quiz',
            correct_option_id=data["correct_id"],
            is_anonymous=False
        )
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
