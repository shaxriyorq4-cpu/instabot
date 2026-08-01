import asyncio
import logging
import os
import re
import yt_dlp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = "8915219066:AAEapW0Id_nw6Ex1hZsm8tcTxmR4x8k-Zag"

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

    file_path = None
    try:
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
            'format': 'best',
            'noplaylist': True,
        }
        
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        file_path = await asyncio.to_thread(download)
    except Exception as e:
        logging.error(f"yt-dlp xatosi: {e}")
        await message.answer(f"❌ Xatolik tafsiloti: {e}")

    if file_path and os.path.exists(file_path):
        try:
            video_file = types.FSInputFile(file_path)
            await message.answer_video(video=video_file, caption="✅ Marhamat, video!")
        except Exception as e:
            await message.answer(f"Videoni yuborishda xatolik: {e}")
        
        try:
            os.remove(file_path)
        except Exception:
            pass
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
