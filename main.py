import logging
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.executor import start_polling

from bot_init import bot, dp
from utils import load_data, save_data, get_user, update_user_points
from admin import notify_admin

# Главное меню
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✍️ Поделиться историей", "📖 Читать истории")
    kb.add("🏆 Топ историй", "🧑‍💼 Профиль")
    kb.add("ℹ️ О боте")
    return kb

# Состояние
class StoryState(StatesGroup):
    waiting_for_text = State()

# /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_data = load_data()
    user = get_user(user_data, message.from_user.id)
    save_data(user_data)

    name = message.from_user.first_name or "друг"
    await message.answer(
        f"👋 Привет, {name}!\n\n"
        "Поделись своей вдохновляющей историей или почитай другие истории 🌟",
        reply_markup=main_menu()
    )

# Написать историю
@dp.message_handler(lambda m: m.text == "✍️ Поделиться историей")
async def ask_story(message: types.Message):
    await message.answer("✍️ Напиши свою добрую или вдохновляющую историю.\nПосле отправки она пройдёт модерацию 🕊️")
    await StoryState.waiting_for_text.set()

@dp.message_handler(state=StoryState.waiting_for_text)
async def receive_story(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if len(text) < 20:
        await message.answer("📏 История слишком короткая. Попробуй написать подробнее.")
        return

    data = load_data()

    story = {
        "text": text,
        "likes": 0,
        "user_id": message.from_user.id,
        "approved": False,
        "liked_by": [],
        "rejected": False
    }

    data["stories"].append(story)
    story_id = len(data["stories"]) - 1

    # Обновим пользователя
    user = get_user(data, message.from_user.id)
    user["submitted"] += 1
    save_data(data)

    await notify_admin(text, story_id, message.from_user.username, message.from_user.id)

    await message.answer("⏳ История отправлена на модерацию!\nОжидай публикации 🙌", reply_markup=main_menu())
    await state.finish()

# Читать истории
@dp.message_handler(lambda m: m.text == "📖 Читать истории")
async def read_stories(message: types.Message):
    data = load_data()
    approved = [s for s in data["stories"] if s["approved"] and not s.get("rejected")]
    if not approved:
        await message.answer("😕 Пока нет одобренных историй.")
        return
    await show_story(message, approved, 0)

def story_markup(index):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("❤️ Лайк", callback_data=f"like_{index}")],
        [InlineKeyboardButton("➡️ Следующая", callback_data=f"next_{index}")]
    ])

async def show_story(msg, stories, index):
    if index >= len(stories):
        await msg.answer("📚 Больше историй нет.", reply_markup=main_menu())
        return

    story = stories[index]
    preview = story["text"][:4096]
    markup = story_markup(index)

    if isinstance(msg, types.CallbackQuery):
        await msg.message.edit_text(preview, reply_markup=markup)
    else:
        await msg.answer(preview, reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data.startswith("like_") or c.data.startswith("next_"))
async def handle_buttons(callback: types.CallbackQuery):
    action, idx = callback.data.split("_")
    idx = int(idx)
    data = load_data()
    approved = [s for s in data["stories"] if s["approved"] and not s.get("rejected")]

    if idx >= len(approved):
        await callback.answer("Ошибка: история не найдена.")
        return

    story = approved[idx]
    full_list = data["stories"]
    real_index = full_list.index(story)

    if action == "like":
        if callback.from_user.id in story["liked_by"]:
            await callback.answer("Ты уже лайкал(а) эту историю 💡", show_alert=True)
            return

        story["likes"] += 1
        story["liked_by"].append(callback.from_user.id)

        # Обновим очки пользователя
        user = get_user(data, callback.from_user.id)
        user["likes_given"] += 1
        update_user_points(user, +1)

        save_data(data)
        await callback.answer("❤️ Спасибо за лайк!")
        await show_story(callback, approved, idx)

    elif action == "next":
        await show_story(callback, approved, idx + 1)

# Топ историй
@dp.message_handler(lambda m: m.text == "🏆 Топ историй")
async def top_stories(message: types.Message):
    data = load_data()
    top = sorted(
        [s for s in data["stories"] if s["approved"] and not s.get("rejected")],
        key=lambda x: x["likes"], reverse=True
    )[:3]

    if not top:
        await message.answer("😕 Пока нет популярных историй.")
        return

    text = "🏆 <b>Топ историй недели:</b>\n\n"
    for i, s in enumerate(top):
        preview = s["text"][:150] + "..." if len(s["text"]) > 150 else s["text"]
        text += f"{i+1}. ❤️ {s['likes']} лайков\n{preview}\n\n"

    await message.answer(text, parse_mode="HTML")

# Профиль
@dp.message_handler(lambda m: m.text == "🧑‍💼 Профиль")
async def profile(message: types.Message):
    data = load_data()
    user = get_user(data, message.from_user.id)

    points = user["kindness_points"]
    if points >= 50:
        rank = "🥇 Золото"
    elif points >= 20:
        rank = "🥈 Серебро"
    else:
        rank = "🥉 Бронза"

    text = (
        f"👤 <b>Профиль:</b>\n"
        f"🏅 Ранг: {rank}\n"
        f"❤️ Поставлено лайков: {user['likes_given']}\n"
        f"📝 Отправлено историй: {user['submitted']}\n"
        f"🌟 Очки доброты: {points}"
    )
    await message.answer(text, parse_mode="HTML")

# О боте
@dp.message_handler(lambda m: m.text == "ℹ️ О боте")
async def about_bot(message: types.Message):
    await message.answer(
        "🤖 Этот бот создан для того, чтобы делиться вдохновляющими и добрыми историями 🕊️\n\n"
        "👥 Истории проходят модерацию\n"
        "🏆 Истории с наибольшим количеством лайков попадают в топ недели\n"
        "📊 Вы зарабатываете очки доброты, ставя лайки\n\n"
        "⚠️ <b>Правила:</b>\n"
        "— Без мата\n"
        "— Без рекламы\n"
        "— Без агрессии\n\n"
        "Разработано с ❤️ специально для душевных людей.",
        parse_mode="HTML"
    )

# Запуск бота
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start_polling(dp, skip_updates=True)
