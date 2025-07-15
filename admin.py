from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import load_data, save_data

ADMIN_ID = 5050707973
STICKER_ID = "CAACAgQAAxkBAAEQqhRodkFgIxuOVo8U7SR54jNPXc4u8wAC-RcAApegmFO3ic78vJPsijYE"

def register_admin_callbacks(dp: types.Dispatcher):
    @dp.callback_query_handler(lambda c: c.data.startswith(("approve_", "decline_")))
    async def on_moderation(c: types.CallbackQuery):
        data = load_data()
        idx = int(c.data.split("_")[1])
        story = data["stories"][idx]
        uid = story["user_id"]
        if c.data.startswith("approve_"):
            story["approved"] = True
            save_data(data)
            await bot.send_sticker(uid, STICKER_ID)
            await bot.send_message(uid, "🎉 Твоя история одобрена и уже видна всем!")
            await send_new_story_notifications(data, story)
            await c.message.edit_text("✅ История одобрена!")
        else:
            save_data(data)
            await bot.send_message(uid, "❌ К сожалению, твоя история отклонена.")
            await c.message.edit_text("🗑 История отклонена.")

    @dp.callback_query_handler(lambda c: c.data == "rules")
    async def on_rules(c: types.CallbackQuery):
        await c.message.edit_text(
            "📋 Правила публикации:\n"
            "1. Только добрые истории.\n"
            "2. Без мата, рекламы, агрессии.\n"
            "3. Пиши от души."
        )

    @dp.message_handler(commands=["admin"])
    async def on_admin(m: types.Message):
        if m.from_user.id != ADMIN_ID:
            await m.reply("⛔ Нет доступа.")
            return
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("📋 Правила / О боте", callback_data="rules"))
        await m.answer("🔧 Админ-панель", reply_markup=kb)
