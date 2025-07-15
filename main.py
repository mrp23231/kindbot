import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import json
from admin import notify_admin, register_admin_callbacks, ADMIN_ID

API_TOKEN = "8148757569:AAFOJAh97I9YKktYPT76_JO_M8khUdWnwcw"  # ← ЗАМЕНИ на свой токен

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class StoryState(StatesGroup):
    waiting_for_text = State()

def load_data():
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"stories": [], "users": {}, "subscriptions": {}, "thanks": {}}

def save_data(data):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main_menu():
    return types.ReplyKeyboardMarkup(resize_keyboard=True).add(
        "📖 Читать истории", "✍️ Поделиться историей",
        "👤 Профиль", "🧱 Стена благодарности"
    )

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id not in data["users"]:
        data["users"][user_id] = {
            "username": message.from_user.username or f"user_{user_id}",
            "thanks": 0,
            "points": 0,
            "badge": ""
        }
        save_data(data)
    await message.answer("Добро пожаловать в бот добрых историй ✨", reply_markup=main_menu())

@dp.message_handler(commands=["admin"])
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет доступа.")
        return
    await register_admin_callbacks(message, bot)

@dp.message_handler(lambda m: m.text == "✍️ Поделиться историей")
async def start_story(message: types.Message):
    await message.answer("📝 Напиши вдохновляющую историю. После модерации она будет опубликована!")
    await StoryState.waiting_for_text.set()

@dp.message_handler(state=StoryState.waiting_for_text)
async def save_story(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if len(text) < 20:
        await message.answer("📏 История слишком короткая. Напиши подробнее.")
        return
    data = load_data()
    story = {
        "text": text,
        "likes": 0,
        "user_id": message.from_user.id,
        "approved": False,
        "liked_by": [],
        "thanks_by": [],
    }
    data["stories"].append(story)
    index = len(data["stories"]) - 1
    save_data(data)
    await notify_admin(text, index, message.from_user.username, message.from_user.id, bot)
    await message.answer("✨ История отправлена на модерацию. Спасибо за доброту 🙏", reply_markup=main_menu())
    await state.finish()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from admin import setup_admin_callbacks
    setup_admin_callbacks(dp)
    executor.start_polling(dp, skip_updates=True)
