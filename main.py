import os
import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)

# Инициализация
TOKEN = os.getenv("TELEGRAM_TOKEN")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=TOKEN)
dp = Dispatcher()

QUIZ_PROMPT = (
    "Ты остроумный ведущий. Придумай 1 вопрос на тему {topic}. "
    "Ответ дай СТРОГО в JSON: "
    '{{"question": "текст(до 250 симв)", "options": ["1","2","3","4"], "correct_id": 0, "expl": "факт"}}'
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Stranger Things  waffle", callback_data="t_Stranger Things")
    builder.button(text="Кино 🍿", callback_data="t_Movies")
    builder.button(text="Свечи и бизнес 🕯", callback_data="t_Candles")
    builder.button(text="Случайный факт 🎲", callback_data="t_General")
    builder.adjust(2)
    await message.answer("Выбери тему квиза:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("t_"))
async def ask_quiz(callback: types.CallbackQuery):
    topic = callback.data.split("_")[1]
    await callback.message.answer(f"⏳ Генерирую вопрос: {topic}...")
    try:
        response = model.generate_content(QUIZ_PROMPT.format(topic=topic))
        # Очистка JSON от возможных артефактов
        txt = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(txt)
        
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
        logging.error(e)
        await callback.message.answer("Ошибка связи с ИИ. Попробуй еще раз!")

@dp.message(Command("meme"))
async def send_meme(message: types.Message):
    res = model.generate_content("Придумай смешную текстовую подпись для мема. Тема: жизнь в Днепре или фанаты сериалов.")
    await message.answer(f"😂 Мем:\n\n{res.text}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
