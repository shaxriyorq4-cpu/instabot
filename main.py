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
        "Instagram'dan istalgan video, rasm, reels va story havolasini yuboring!\n\n"
        "🚀 Havolani yuboring!"
    )

@dp.message()
async def process_link_handler(message: types.Message):
    text = message.text
    match = URL_REGEX.search(text)
    
    if not match:
        return

    url = match.group(0)
    processing_msg = await message.answer("⏳ Yuklab olinmoqda, iltimos kuting...")

    file_path = None
    error_message = None

    try:
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
            'format': 'best',
            'noplaylist': True,
            'cookiefile': 'cookies.txt',
        }
        
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        file_path = await asyncio.to_thread(download)
    except Exception as e:
        error_message = str(e)
        logging.error(f"yt-dlp xatosi: {e}")

    if file_path and os.path.exists(file_path):
        try:
            if file_path.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                media_file = types.FSInputFile(file_path)
                await message.answer_photo(photo=media_file, caption="✅ Marhamat, rasm!")
            else:
                media_file = types.FSInputFile(file_path)
                await message.answer_video(video=media_file, caption="✅ Marhamat, video!")
        except Exception as e:
            await message.answer(f"❌ Faylni yuborishda xatolik: {e}")
        
        try:
            os.remove(file_path)
        except Exception:
            pass
    else:
        if error_message:
            await message.answer(f"❌ Xatolik tafsiloti:\n<code>{error_message}</code>", parse_mode="HTML")
        else:
            await message.answer("❌ Kechirasiz, faylni yuklab bo'lmadi.")

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
    except Exception:
        pass

async def main():
    logging.info("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
