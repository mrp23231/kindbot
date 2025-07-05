from aiogram import Bot, Dispatcher, executor, types

TOKEN = "8148757569:AAFOJAh97I9YKktYPT76_JO_M8khUdWnwcw"  # Замени на свой токен
ADMIN_ID = 5050707973      # Твой Telegram ID (число)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['moderate'])
async def moderate(message: types.Message):
    print(f"/moderate вызван от {message.from_user.id}")
    if message.from_user.id != ADMIN_ID:
        await message.answer("У тебя нет доступа к модерации.")
        return
    await message.answer("Доступ к модерации подтверждён!")

@dp.message_handler()
async def debug_messages(message: types.Message):
    print(f"Получено сообщение: {message.text} от {message.from_user.id}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
