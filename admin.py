from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext

ADMIN_ID = 5050707973
STICKER_ID = "CAACAgQAAxkBAAEQqhRodkFgIxuOVo8U7SR54jNPXc4u8wAC-RcAApegmFO3ic78vJPsijYE"

def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("👑 Назначить Автора недели", callback_data="set_author_week")],
        [InlineKeyboardButton("📋 Правила", callback_data="show_rules")]
    ])

async def notify_admin(text, index, username, user_id, bot):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{index}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{index}")
        ]
    ])
    await bot.send_message(ADMIN_ID, f"Новая история от @{username or user_id} (ID: {user_id}):\n\n{text}", reply_markup=markup)

async def register_admin_callbacks(message, bot):
    await message.answer("👮 Админ-панель", reply_markup=admin_keyboard())

def setup_admin_callbacks(dp: Dispatcher):
    @dp.callback_query_handler(lambda c: c.data.startswith("approve_") or c.data.startswith("reject_"))
    async def moderate_story(callback: types.CallbackQuery):
        from main import load_data, save_data
        data = load_data()
        idx = int(callback.data.split("_")[1])
        story = data["stories"][idx]
        author_id = story["user_id"]

        if callback.data.startswith("approve_"):
            story["approved"] = True
            save_data(data)
            await callback.bot.send_message(author_id, "🎉 Твоя история одобрена и уже видна всем в боте!")
            await callback.bot.send_sticker(author_id, STICKER_ID)
            await callback.answer("История одобрена ✅")
        else:
            data["stories"].pop(idx)
            save_data(data)
            await callback.bot.send_message(author_id, "😔 К сожалению, твоя история была отклонена. Попробуй ещё раз с соблюдением правил.")
            await callback.answer("История отклонена ❌")

    @dp.callback_query_handler(lambda c: c.data == "show_rules")
    async def show_rules(callback: types.CallbackQuery):
        await callback.answer()
        await callback.message.answer("📋 Правила публикации:\n\n— История должна быть доброй\n— Не менее 20 символов\n— Без спама и рекламы")

    @dp.callback_query_handler(lambda c: c.data == "set_author_week")
    async def set_author(callback: types.CallbackQuery):
        await callback.answer("⚙️ Функция назначения пока в разработке.")
