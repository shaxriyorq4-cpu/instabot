from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import asyncio

TOKEN = "8915219066:AAGSCkzvFImev5HLBdOMqv-q8CWjraGnsHg"

bot = Bot(TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Salom 👋")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
