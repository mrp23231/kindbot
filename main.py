import logging
import asyncio
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.executor import start_polling

from bot_init import bot, dp
from config import TOKEN
from utils import load_data, save_data
from admin import notify_admin

# Меню
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✍️ Поделиться историей")
    kb.add("📖 Читать истории", "🏆 Топ историй")
    return kb

# Состояния
class StoryState(StatesGroup):
    waiting_for_text = State()

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    name = message.from_user.username or message.from_user.first_name or "друг"
    await message.answer(f"Привет, {name}! Поделись вдохновляющей историей или почитай другие:", reply_markup=main_menu())

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

# Кнопки под историей
def story_markup(story_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("❤️ Лайк", callback_data=f"like_{story_id}")],
        [InlineKeyboardButton("➡️ Следующая", callback_data=f"next_{story_id}")]
    ])

# Показать одну историю
async def show_story(msg, stories, current_id):
    if current_id >= len(stories):
        await msg.answer("История не найдена.")
        return
    story = stories[current_id]
    if not story.get("approved"):
        await msg.answer("Эта история ещё не одобрена.")
        return
    text = story["text"][:4096]
    markup = story_markup(current_id)
    if isinstance(msg, types.CallbackQuery):
        await msg.message.edit_text(text, reply_markup=markup)
    else:
        await msg.answer(text, reply_markup=markup)

# Читать истории
@dp.message_handler(lambda m: m.text == "📖 Читать истории")
async def read_stories(message: types.Message):
    data = load_data()
    approved = [i for i, s in enumerate(data["stories"]) if s.get("approved")]
    if not approved:
        await message.answer("Пока нет одобренных историй 😔")
        return
    await show_story(message, data["stories"], approved[0])

# Обработка кнопок лайка/следующей
@dp.callback_query_handler(lambda c: c.data.startswith("like_") or c.data.startswith("next_"))
async def story_buttons(callback: types.CallbackQuery):
    action, story_id = callback.data.split("_")
    story_id = int(story_id)
    data = load_data()

    if story_id >= len(data["stories"]):
        await callback.answer("История не найдена.")
        return

    story = data["stories"][story_id]
    if not story.get("approved"):
        await callback.answer("История не одобрена.")
        return

    if action == "like":
        user_id = callback.from_user.id
        if user_id in story.get("liked_by", []):
            await callback.answer("Вы уже лайкнули эту историю.")
        else:
            story["likes"] += 1
            story.setdefault("liked_by", []).append(user_id)
            save_data(data)
            await callback.answer("Спасибо за лайк ❤️")
        await show_story(callback, data["stories"], story_id)

    elif action == "next":
        next_id = story_id + 1
        while next_id < len(data["stories"]):
            if data["stories"][next_id].get("approved"):
                await show_story(callback, data["stories"], next_id)
                return
            next_id += 1
        await callback.answer("Это была последняя история.")
        await callback.message.edit_text("Больше историй нет.", reply_markup=main_menu())

# Топ историй
@dp.message_handler(lambda m: m.text == "🏆 Топ историй")
async def top_stories(message: types.Message):
    data = load_data()
    top = sorted(
        [s for s in data["stories"] if s.get("approved")],
        key=lambda x: x.get("likes", 0),
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

# Запуск
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(bot.delete_webhook(drop_pending_updates=True))
    start_polling(dp, skip_updates=True)
