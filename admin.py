from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import load_data, save_data

ADMIN_ID = 5050707973
STICKER_ID = "CAACAgQAAxkBAAEQqhRodkFgIxuOVo8U7SR54jNPXc4u8wAC-RcAApegmFO3ic78vJPsijYE"

async def notify_admin(bot, text, story_idx, username, user_id):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{story_idx}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"decline_{story_idx}")
    )
    await bot.send_message(ADMIN_ID,
        f"📝 Новая история от @{username} (ID: {user_id}):\n\n{text}",
        reply_markup=kb
    )

def register_admin_callbacks(dp: Dispatcher):
    @dp.callback_query_handler(lambda c: c.data.startswith(("approve_", "decline_")))
    async def on_moderation(c: types.CallbackQuery):
        from main import bot, send_new_story_notifications  # локальный импорт, чтобы избежать циклов
        data = load_data()
        idx = int(c.data.split("_")[1])
        story = data["stories"][idx]
        uid = story["user_id"]
        if c.data.startswith("approve_"):
            story["approved"] = True
            save_data(data)
            await bot.send_sticker(uid, STICKER_ID)
            await bot.send_message(uid, "🎉 Твоя история одобрена и уже видна всем в боте!")
            await send_new_story_notifications(data, story)
            await c.message.edit_text("✅ История одобрена!")
        else:
            await bot.send_message(uid, "❌ К сожалению, твоя история была отклонена. Попробуй ещё раз с соблюдением правил.")
            await c.message.edit_text("🗑 История отклонена.")

    @dp.callback_query_handler(lambda c: c.data == "rules")
    async def on_rules(c: types.CallbackQuery):
        await c.message.edit_text(
            "📋 <b>Правила публикации историй:</b>\n\n"
            "1. История должна быть доброй, светлой и искренней.\n"
            "2. Без оскорблений, негатива, мата или рекламы.\n"
            "3. Только авторский текст, минимум 20 символов.\n"
            "4. Истории проходят ручную модерацию.\n"
            "\nСпасибо за добрые поступки! ❤️", parse_mode="HTML"
        )

    @dp.message_handler(commands=["admin"])
    async def on_admin(m: types.Message):
        if m.from_user.id != ADMIN_ID:
            await m.reply("⛔ У тебя нет доступа к админке.")
            return
        kb = InlineKeyboardMarkup().add(
            InlineKeyboardButton("📋 Правила / О боте", callback_data="rules")
        )
        await m.answer("🔧 Админ-панель активна.", reply_markup=kb)
