import logging
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.executor import start_polling

from bot_init import bot, dp
from utils import load_data, save_data
from admin import notify_admin

# Главное меню
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✍️ Поделиться историей")
    kb.add("📖 Читать истории", "🏆 Топ историй")
    return kb

# Состояния
class StoryState(StatesGroup):
    waiting_for_text = State()

# /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    name = message.from_user.username or message.from_user.first_name or "друг"
    await message.answer(f"Привет, {name}! Поделись вдохновляющей историей или почитай другие:", reply_markup=main_menu())

# Написать историю
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
    story = {
        "text": text,
        "likes": 0,
        "user_id": message.from_user.id,
        "approved": False,
        "liked_by": []
    }
    data["stories"].append(story)
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

    story = approved[idx]
    all_stories = data["stories"]
    story_index = all_stories.index(story)

    if action == "like":
        if callback.from_user.id in all_stories[story_index]["liked_by"]:
            await callback.answer("Ты уже лайкал(а) эту историю 💡", show_alert=True)
            return
        all_stories[story_index]["likes"] += 1
        all_stories[story_index]["liked_by"].append(callback.from_user.id)
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

# Запуск бота
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start_polling(dp, skip_updates=True)
