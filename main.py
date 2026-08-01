import asyncio
import logging
import os
import re
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

# Tokenni Railway'dagi Variables (BOT_TOKEN) dan avtomatik o'qiydi
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

URL_REGEX = re.compile(
    r'http[s]?://(?:[a-zA-Z0-9$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Salom! 👋\n\n"
        "Men Instagram va boshqa tarmoqlardan videolarni yuklab beraman.\n\n"
        "🚀 Havolani yuboring!"
    )

@dp.message()
async def process_link_handler(message: types.Message):
    text = message.text
    match = URL_REGEX.search(text)
    
    if not match:
        return

    url = match.group(0)
    processing_msg = await message.answer("⏳ Media yuklab olinmoqda, iltimos kuting...")

    video_url = None
    try:
        api_url = f"https://tikwm.com/api/?url={url}"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                res = await resp.json()
                if res.get("code") == 0:
                    video_url = res["data"].get("play")
    except Exception as e:
        logging.error(f"API xatosi: {e}")

    if not video_url:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://co.wuk.sh/api/json",
                    json={"url": url, "vQuality": "max"},
                    headers={"Accept": "application/json"}
                ) as resp:
                    res = await resp.json()
                    if res.get("status") == "stream" or res.get("status") == "redirect":
                        video_url = res.get("url")
        except Exception as e:
            logging.error(f"Cobalt API xatosi: {e}")

    if video_url:
        try:
            await message.answer_video(video=video_url, caption="✅ Marhamat, video!")
        except Exception as e:
            await message.answer(f"Videoni yuborishda xatolik: {e}")
    else:
        await message.answer("❌ Kechirasiz, videoni yuklab bo'lmadi. Havolani tekshirib qaytadan yuboring.")

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id + 1)
    except Exception:
        pass

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
    except Exception:
        pass

async def main():
    logging.info("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
