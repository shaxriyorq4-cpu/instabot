import asyncio
import logging
import os
import re
import uuid
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
import yt_dlp

# ==========================================
# LOYIHA SOZLAMALARI (CONFIGURATIONS)
# ==========================================

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

# ==========================================
# YUKLASH FUNKSIYASI
# ==========================================

def download_media_sync(url: str, user_id: int) -> dict:
    folder_prefix = os.path.join(DOWNLOAD_DIR, f"user_{user_id}_{uuid.uuid4().hex[:6]}")
    os.makedirs(folder_prefix, exist_ok=True)
    
    output_template = os.path.join(folder_prefix, "video.%(ext)s")
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'extractor_args': {'instagram': {'api_json': True}},
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    video_path = None
    title = "Media"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Media')
            filename = ydl.prepare_filename(info)
            
            if os.path.exists(filename):
                video_path = filename
    except Exception as e:
        logging.error(f"Yuklashda xatolik: {e}")

    return {
        'folder': folder_prefix,
        'video_path': video_path,
        'audio_path': None,
        'title': title
    }

# ==========================================
# BOT HANDLERLARI
# ==========================================

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Salom! 👋\n\n"
        "Men Instagram (Post, Reels, Karusel, Story), TikTok va YouTube'dan videolarni yuklab beraman.\n\n"
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

    data = await asyncio.to_thread(download_media_sync, url, message.from_user.id)
    
    video_path = data.get('video_path')
    folder = data.get('folder')

    if video_path and os.path.exists(video_path):
        try:
            file = FSInputFile(video_path)
            await message.answer_video(video=file, caption="✅ Marhamat, video!")
        except Exception as e:
            await message.answer(f"Videoni yuborishda xatolik yuz berdi: {e}")
    else:
        await message.answer("❌ Kechirasiz, videoni yuklab bo'lmadi. Havola yopiq yoki mavjud emas.")

    # Fayllarni tozalash
    try:
        if folder and os.path.exists(folder):
            for f in os.listdir(folder):
                os.remove(os.path.join(folder, f))
            os.rmdir(folder)
    except Exception:
        pass

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
    except Exception:
        pass

# ==========================================
# ASOSIY FUNKSIYA
# ==========================================

async def main():
    logging.info("Bot ishga tushdi...")
    await dp.start_polling(bot)

if name == "__main__":
    asyncio.run(main())
