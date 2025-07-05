import json
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

TOKEN = "8148757569:AAFOJAh97I9YKktYPT76_JO_M8khUdWnwcw"  # Замени на свой токен
ADMIN_ID = 5050707973      # Твой Telegram ID (число)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# -------------------- Работа с данными --------------------

def load_data():
    try:
        with open("database.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"stories": []}

def save_data(data):
    with open("database.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -------------------- Клавиатура --------------------

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✍️ Поделиться историей")
    kb.add("📖 Читать истории", "🏆 Топ историй")
    return kb

# -------------------- FSM --------------------

class StoryState(StatesGroup):
    waiting_for_text = State()

# -------------------- Админ уведомление --------------------

async def notify_admin(text, story_index, username, user_id):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{story_index}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{story_index}")]
    ])
    try:
        await bot.send_message(
            ADMIN_ID,
            f"Новая история от @{username or user_id}:\n\n{text[:4000]}",
            reply_markup=markup
        )
    except Exception as e:
        logging.error(f"Не удалось отправить уведомление администратору: {e}")

# -------------------- Команды --------------------

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    name = message.from_user.username or message.from_user.first_name or "друг"
    await message.answer(f"Привет, {name}! Я здесь, чтобы поддержать тебя. Выбери действие 👇", reply_markup=main_menu())

# -------------------- Отправка истории --------------------

@dp.message_handler(lambda m: m.text == "✍️ Поделиться историей")
async def start_sending_story(message: types.Message):
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
    story_index = len(data["stories"]) - 1
    save_data(data)
    await notify_admin(text, story_index, message.from_user.username, message.from_user.id)
    await message.answer("Спасибо! Твоя история отправлена на модерацию ✨", reply_markup=main_menu())
    await state.finish()

# -------------------- Модерация --------------------

def moderation_markup(index):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{index}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{index}")],
        [InlineKeyboardButton("➡️ Далее", callback_data=f"nextmod_{index}")]
    ])

async def show_pending_story(msg, data, index):
    pending = [s for s in data["stories"] if not s["approved"]]
    if index >= len(pending):
        await msg.answer("Модерация завершена.")
        return

    story = pending[index]
    markup = moderation_markup(index)
    text = story["text"][:4096]

    if isinstance(msg, types.CallbackQuery):
        await msg.message.edit_text(text, reply_markup=markup)
    else:
        await msg.answer(text, reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith(("approve_", "reject_", "nextmod_")))
async def handle_moderation(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Недостаточно прав.")
        return

    action, idx = callback.data.split("_")
    idx = int(idx)

    data = load_data()
    pending = [s for s in data["stories"] if not s["approved"]]

    if idx >= len(pending):
        await callback.answer("История не найдена.")
        return

    story = pending[idx]

    if action == "approve":
        story["approved"] = True
        save_data(data)
        await callback.answer("✅ Одобрено")
        await show_pending_story(callback, data, idx + 1)

    elif action == "reject":
        data["stories"].remove(story)
        save_data(data)
        await callback.answer("❌ Удалено")
        await show_pending_story(callback, data, idx)

    elif action == "nextmod":
        await callback.answer()
        await show_pending_story(callback, data, idx + 1)

# -------------------- Просмотр историй --------------------

@dp.message_handler(lambda m: m.text == "📖 Читать истории")
async def read_stories(message: types.Message):
    data = load_data()
    approved = [s for s in data["stories"] if s["approved"]]
    if not approved:
        await message.answer("Пока нет одобренных историй 😔")
        return
    await show_story(message, approved, 0)

def story_markup(index):
    buttons = [
        [InlineKeyboardButton("❤️ Лайк", callback_data=f"like_{index}")],
        [InlineKeyboardButton("➡️ Следующая", callback_data=f"next_{index}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

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
async def handle_story_buttons(callback: types.CallbackQuery):
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

# -------------------- Топ историй --------------------

@dp.message_handler(lambda m: m.text == "🏆 Топ историй")
async def top_stories(message: types.Message):
    data = load_data()
    top = sorted(
        [s for s in data["stories"] if s["approved"]],
        key=lambda x: x["likes"],
        reverse=True
    )[:3]
    if not top:
        await message.answer("Пока нет популярных историй.")
        return

    text = "🏆 Топ историй недели:\n\n"
    for i, s in enumerate(top):
        preview = s["text"][:150] + "..." if len(s["text"]) > 150 else s["text"]
        text += f"{i+1}. ❤️ {s['likes']} лайков\n{preview}\n\n"
    await message.answer(text)

# -------------------- Запуск --------------------

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
