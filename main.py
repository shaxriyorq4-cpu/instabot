import asyncio
import logging
import os
import re
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = "8939497082:AAF17GbWpTo4NpTiFaJ6M_0KyhemuKrN0ns"

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
        # Bepul vaishonchli API orqali video havolasini olamiz
        api_url = f"https://tikwm.com/api/?url={url}"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                res = await resp.json()
                if res.get("code") == 0:
                    video_url = res["data"].get("play")
    except Exception as e:
        logging.error(f"API xatosi: {e}")

    if not video_url:
        # Agar bu TikTok yoki boshqa bo'lmasa, Cobalt API orqali urinib ko'ramiz
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
        await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
    except Exception:
        pass

async def main():
    logging.info("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
