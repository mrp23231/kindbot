import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from admin import notify_admin, register_admin_callbacks
from utils import load_data, save_data, get_user, get_badge, main_menu

API_TOKEN = "8148757569:AAFOJAh97I9YKktYPT76_JO_M8khUdWnwcw"  # ← вставь токен

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class StoryState(StatesGroup):
    waiting_for_text = State()


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    data = load_data()
    get_user(data, message.from_user.id, message.from_user.username)
    save_data(data)
    await message.answer("👋 Добро пожаловать в KindBot — мини‑сеть добрых историй!", reply_markup=main_menu())


@dp.message_handler(lambda m: m.text == "✍️ Поделиться историей")
async def cmd_share(message: types.Message):
    await message.answer("📝 Напиши вдохновляющую историю. После модерации она будет опубликована!")
    await StoryState.waiting_for_text.set()


@dp.message_handler(state=StoryState.waiting_for_text)
async def on_share(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if len(text) < 20:
        await message.answer("📏 История слишком короткая. Напиши подробнее.")
        return
    data = load_data()
    story = {
        "text": text,
        "likes": 0,
        "thanks": 0,
        "user_id": message.from_user.id,
        "approved": False,
        "liked_by": [],
        "thanked_by": []
    }
    data["stories"].append(story)
    idx = len(data["stories"]) - 1
    save_data(data)
    await notify_admin(bot, text, idx, message.from_user.username, message.from_user.id)
    await message.answer("✨ История отправлена на модерацию. Спасибо за доброту!", reply_markup=main_menu())
    await state.finish()


def make_story_markup(idx, story, viewer_id, data):
    liked = viewer_id in story["liked_by"]
    thanked = viewer_id in story["thanked_by"]
    subbed = str(viewer_id) in data.get("subscriptions", {}) and str(story["user_id"]) in data["subscriptions"][str(viewer_id)]
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❤️ Лайк", callback_data=f"like_{idx}"))
    kb.add(types.InlineKeyboardButton("🙏 Спасибо", callback_data=f"thank_{idx}"))
    kb.add(types.InlineKeyboardButton("🔔 Подписаться" if not subbed else "🔕 Отписаться", callback_data=f"sub_{story['user_id']}"))
    kb.add(types.InlineKeyboardButton("➡️ Следующая", callback_data=f"next_{idx}"))
    return kb


@dp.message_handler(lambda m: m.text == "📖 Читать истории")
async def cmd_read(message: types.Message):
    data = load_data()
    approved = [s for s in data["stories"] if s["approved"]]
    if not approved:
        await message.answer("😔 Пока нет историй.")
        return
    story = approved[0]
    markup = make_story_markup(0, story, message.from_user.id, data)
    await message.answer(story["text"], reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data.startswith(("like_", "thank_", "sub_", "next_")))
async def cq_actions(c: types.CallbackQuery):
    data = load_data()
    parts = c.data.split("_")
    action = parts[0]
    viewer = c.from_user.id

    if action in ("like", "thank", "next"):
        idx = int(parts[1])
        story = [s for s in data["stories"] if s["approved"]][idx]
        global_idx = data["stories"].index(story)
        if action == "like":
            if viewer in story["liked_by"]:
                await c.answer("✅ Уже лайкал", show_alert=True)
            else:
                story["likes"] += 1
                story["liked_by"].append(viewer)
                save_data(data)
                await c.answer("❤️ Спасибо за лайк!")
        elif action == "thank":
            if viewer in story["thanked_by"]:
                await c.answer("✅ Уже отправлял спасибо", show_alert=True)
            else:
                story["thanks"] += 1
                story["thanked_by"].append(viewer)
                data["users"][str(story["user_id"])]["points"] += 1
                data["users"][str(story["user_id"])]["thanks"] += 1
                save_data(data)
                await c.answer("🙏 Спасибо отправлено!")
        elif action == "next":
            await cmd_read(c.message)

        # обновляем сообщение
        data = load_data()
        story = [s for s in data["stories"] if s["approved"]][idx]
        markup = make_story_markup(idx, story, viewer, data)
        await c.message.edit_text(story["text"], reply_markup=markup)

    elif action == "sub":
        author = parts[1]
        subs = data.setdefault("subscriptions", {})
        subs.setdefault(str(viewer), [])
        if author in subs[str(viewer)]:
            subs[str(viewer)].remove(author)
            await c.answer("🔕 Отписался")
        else:
            subs[str(viewer)].append(author)
            await c.answer("🔔 Подписка оформлена")
        save_data(data)
        # не обновляем текст

@dp.message_handler(lambda m: m.text == "👤 Профиль")
async def cmd_profile(m: types.Message):
    data = load_data()
    user = get_user(data, m.from_user.id)
    badge = get_badge(user, m.from_user.id, data)
    text = (f"👤 Профиль @{user['username']}\n"
            f"✨ Очки доброты: {user['points']}\n"
            f"🙏 Спасибо получено: {user['thanks']}\n"
            f"🏅 Бейдж: {badge or '—'}")
    await m.answer(text)

@dp.message_handler(lambda m: m.text == "🧱 Стена благодарности")
async def cmd_wall(m: types.Message):
    data = load_data()
    tops = sorted(data["users"].values(), key=lambda u: u["thanks"], reverse=True)[:5]
    if not tops:
        await m.answer("Пока никто не получил «Спасибо»")
        return
    text = "🧱 Стена благодарности:\n\n"
    for u in tops:
        text += f"@{u['username']} — 🙏 {u['thanks']}\n"
    await m.answer(text)

@dp.message_handler(commands=["admin"])
async def cmd_admin(m: types.Message):
    await register_admin_callbacks(dp)  # регистрируем, если не сделано
    await types.Chat(id=m.chat.id).send_message("🔧 Админ-панель активирована")

async def send_new_story_notifications(data, story):
    author = str(story["user_id"])
    for u, subs in data.get("subscriptions", {}).items():
        if author in subs:
            keyboard = types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("📖 Открыть историю", callback_data=f"open_{data['stories'].index(story)}")
            )
            await bot.send_message(int(u), f"🔔 @{data['users'][author]['username']} опубликовал новую историю!", reply_markup=keyboard)

register_admin_callbacks(dp)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
