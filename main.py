import os
import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import google.generativeai as genai

# Включаем логи, чтобы видеть ошибки в панели Render
logging.basicConfig(level=logging.INFO)

# Ключи
TOKEN = os.getenv("TELEGRAM_TOKEN")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Промпты
QUIZ_PROMPT = (
    "Ты остроумный ведущий. Придумай 1 вопрос на тему {topic}. "
    "Ответ дай СТРОГО в JSON: "
    '{{"question": "текст(до 250 симв)", "options": ["1","2","3","4"], "correct_id": 0, "expl": "факт"}}'
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    # Твои темы
    builder.button(text="Stranger Things 🧇", callback_data="t_Stranger Things")
    builder.button(text="Кино 🍿", callback_data="t_Movies")
    builder.button(text="Свечи и бизнес 🕯", callback_data="t_Candles")
    builder.button(text="Случайный факт 🎲", callback_data="t_General")
    builder.adjust(2)
    
    await message.answer("Привет! Выбери тему для квиза:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("t_"))
async def ask_quiz(callback: types.CallbackQuery):
    topic = callback.data.split("_")[1]
    await callback.message.answer(f"⏳ Генерирую вопрос по теме: {topic}...")
    
    try:
        response = model.generate_content(QUIZ_PROMPT.format(topic=topic))
        data = json.loads(response.text.replace("```json", "").replace("```", "").strip())
        
        await bot.send_poll(
            chat_id=callback.message.chat.id,
            question=data["question"][:300],
            options=[str(opt)[:100] for opt in data["options"][:10]],
            type='quiz',
            correct_option_id=int(data["correct_id"]),
            explanation=data.get("expl", "Крутой факт!")[:200],
            is_anonymous=False
        )
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await callback.message.answer("Бот задумался, попробуй еще раз!")

@dp.message(Command("meme"))
async def send_meme(message: types.Message):
    res = model.generate_content("Придумай смешную подпись для мема про Stranger Things или бизнес на свечах. Только текст.")
    await message.answer(f"😂 Мем дня:\n\n{res.text}")

# Чтобы Render не закрывал приложение по ошибке портов
async def server_stub():
    from aiohttp import web
    app = web.Application()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8080)))
    await site.start()

async def main():
    # Запускаем "заглушку" порта и бота одновременно
    await asyncio.gather(server_stub(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
