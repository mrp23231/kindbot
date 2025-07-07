from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot_init import bot, dp
from utils import load_data, save_data

ADMIN_ID = 5050707973  # ← замените на свой Telegram ID

# Отправка истории админу с кнопками одобрения/отклонения
async def notify_admin(text, story_id, username, user_id):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{story_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{story_id}")
        ]
    ])
    preview = text[:4096]
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📝 Новая история от @{username or 'пользователь'} (ID: {user_id}):\n\n{preview}",
        reply_markup=markup
    )

# Обработка кнопок модерации
@dp.callback_query_handler(lambda c: c.data.startswith("approve_") or c.data.startswith("reject_"))
async def handle_moderation(callback: types.CallbackQuery):
    action, story_id = callback.data.split("_")
    story_id = int(story_id)

    data = load_data()
    if story_id >= len(data["stories"]):
        await callback.answer("История не найдена.")
        return

    story = data["stories"][story_id]

    if action == "approve":
        story["approved"] = True
        await callback.message.edit_reply_markup()  # удаляем кнопки
        await callback.answer("История одобрена ✅")
        await callback.message.edit_text("✅ История одобрена и будет отображаться в боте.")

    elif action == "reject":
        data["stories"][story_id]["rejected"] = True  # просто помечаем как отклонённую
        await callback.answer("История отклонена ❌")
        await callback.message.edit_text("❌ История была отклонена и не будет опубликована.")

    save_data(data)
