from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from main import dp, load_data, save_data

ADMIN_ID =5050707973 # Замените на свой Telegram ID

def moderation_markup(index):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{index}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{index}")],
        [InlineKeyboardButton("➡️ Далее", callback_data=f"nextmod_{index}")]
    ])

async def notify_admin(story_text, story_index, username, user_id):
    if not ADMIN_ID:
        return
    text = (
        f"Новая история от @{username or user_id}:\n\n"
        f"{story_text[:1000]}..."
    )
    await dp.bot.send_message(ADMIN_ID, text, reply_markup=moderation_markup(story_index))

@dp.message_handler(commands=['moderate'])
async def moderate(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У тебя нет доступа к модерации.")
        return

    data = load_data()
    pending = [s for s in data["stories"] if not s["approved"]]
    if not pending:
        await message.answer("Нет историй на модерацию.")
        return

    await show_pending_story(message, data, 0)

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
