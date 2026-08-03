from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import asyncio

TOKEN = "8915219066:AAEuLDjgIIkQrKNjI6pmQKC04FqTPYowDQY"

bot = Bot(TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Salom! @instadown_v2_bot ga xush kelibsiz. 🤝 ishni boshlaymizmi!")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
