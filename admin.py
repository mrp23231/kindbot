from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from main import bot, dp, load_data, save_data

def moderation_markup(index):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{index}")],
        [InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{index}")],
        [InlineKeyboardButton("➡️ Далее", callback_data=f"nextmod_{index}")]
    ])

async def notify_admin(text, index, username, user_id):
    msg = f"📝 Новая история от @{username or 'пользователь'} (ID: {user_id}):\n\n{text[:4000]}"
    await bot.send_message(ADMIN_ID, msg, reply_markup=moderation_markup(index))

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
        await callback.message.edit_reply_markup(reply_markup=None)
    elif action == "reject":
        data["stories"].remove(story)
        save_data(data)
        await callback.answer("❌ Удалено")
        await callback.message.edit_reply_markup(reply_markup=None)
    elif action == "nextmod":
        await callback.answer("Следующая история ⏭️")
        await callback.message.edit_text("Ожидаем следующую историю...")
