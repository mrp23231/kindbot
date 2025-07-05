import json
import logging
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import TOKEN
from admin import notify_admin, ADMIN_ID

# Инициализация
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Работа с JSON
def load_data():
    try:
        with open("database.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"stories": []}

def save_data(data):
    with open("database.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Клавиатура
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✍️ Поделиться историей")
    kb.add("📖 Читать истории", "🏆 Топ историй")
    return kb

# Состояния
class StoryState(StatesGroup):
    waiting_for_text = State()

# Команда /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    name = message.from_user.username or message.from_user.first_name or "друг"
    await message.answer(f"Привет, {name}! Я здесь, чтобы поддержать тебя. Выбери действие 👇", reply_markup=main_menu())

# Поделиться историей
@dp.message_handler(lambda m: m.text == "✍️ Поделиться историей")
async def start_story(message: types.Message):
    await message.answer("Напиши свою добрую или вдохновляющую историю. Мы добавим её после модерации 🕊️")
    await StoryState.waiting_for_text.set()

@dp.message_handler(state=StoryState.waiting_for_text)
async def save_story(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if len(text) < 20:
        await message.answer("История слишком короткая. Пожалуйста, напиши подробнее.")
        return
    data = load_data()
    data["stories"].append({
        "text": text,
        "likes": 0,
        "user_id": message.from_user.id,
        "approved": False
    })
    index = len(data["stories"]) - 1
    save_data(data)
    await notify_admin(text, index, message.from_user.username, message.from_user.id)
    await message.answer("Спасибо! Твоя история отправлена на модерацию ✨", reply_markup=main_menu())
    await state.finish()

# Читать истории
@dp.message_handler(lambda m: m.text == "📖 Читать истории")
async def read_stories(message: types.Message):
    data = load_data()
    approved = [s for s in data["stories"] if s["approved"]]
    if not approved:
        await message.answer("Пока нет одобренных историй 😔")
        return
    await show_story(message, approved, 0)

def story_markup(index):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("❤️ Лайк", callback_data=f"like_{index}")],
        [InlineKeyboardButton("➡️ Следующая", callback_data=f"next_{index}")]
    ])

async def show_story(msg, stories, index):
    if index >= len(stories):
        await msg.answer("Больше историй нет.", reply_markup=main_menu())
        return
    story = stories[index]
    text = story["text"][:4096]
    markup = story_markup(index)
    if isinstance(msg, types.CallbackQuery):
        await msg.message.edit_text(text, reply_markup=markup)
    else:
        await msg.answer(text, reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith("like_") or c.data.startswith("next_"))
async def story_buttons(callback: types.CallbackQuery):
    action, idx = callback.data.split("_")
    idx = int(idx)
    data = load_data()
    approved = [s for s in data["stories"] if s["approved"]]
    if idx >= len(approved):
        await callback.answer("История не найдена.")
        return
    if action == "like":
        approved[idx]["likes"] += 1
        save_data(data)
        await callback.answer("Спасибо за лайк ❤️")
        await show_story(callback, approved, idx)
    elif action == "next":
        await show_story(callback, approved, idx + 1)

# Топ историй
@dp.message_handler(lambda m: m.text == "🏆 Топ историй")
async def top_stories(message: types.Message):
    data = load_data()
    top = sorted([s for s in data["stories"] if s["approved"]], key=lambda x: x["likes"], reverse=True)[:3]
    if not top:
        await message.answer("Пока нет популярных историй.")
        return
    text = "🏆 Топ историй недели:\n\n"
    for i, s in enumerate(top):
        preview = s["text"][:150] + "..." if len(s["text"]) > 150 else s["text"]
        text += f"{i+1}. ❤️ {s['likes']} лайков\n{preview}\n\n"
    await message.answer(text)

# Удаляем webhook при запуске
if __name__ == '__main__':
    async def on_startup():
        await bot.delete_webhook(drop_pending_updates=True)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_startup())
    executor.start_polling(dp, skip_updates=True)
