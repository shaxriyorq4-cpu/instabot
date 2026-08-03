import os
import shutil
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
import yt_dlp

TOKEN = "8915219066:AAGSCkzvFImev5HLBdOMqv-q8CWjraGnsHg"

bot = Bot(token=TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


@dp.message(commands=["start"])
async def start_handler(message: types.Message):
    # /start bosilganda hech narsa yozmaydi
    pass


async def download_video(url: str, folder: str):
    """Tezkor yuklab olish funksiyasi"""
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(folder, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'remote_components': ['ejs:github'],
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'skip': ['hls', 'dash']
                }
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if os.path.exists(filename):
                return filename
                
            for f in os.listdir(folder):
                full_path = os.path.join(folder, f)
                if os.path.isfile(full_path):
                    return full_path
                    
    except Exception as e:
        print(f"Yuklashda xato: {e}")
    return None


@dp.message()
async def link_handler(message: types.Message):
    if not message.text:
        return
        
    url = message.text.strip()
    
    if not url.startswith(("http://", "https://")):
        await message.answer("❌ Xatolik: Iltimos to'g'ri link yuboring!")
        return

    # To'g'ri havola bo'lsa hech qanday matn yozmaydi, faqatgina video yuklaydi
    user_folder = os.path.join(DOWNLOAD_DIR, str(message.from_user.id))
    os.makedirs(user_folder, exist_ok=True)

    try:
        video_path = await download_video(url, user_folder)

        if video_path and os.path.exists(video_path):
            video_file = FSInputFile(video_path)
            
            # Videoni hech qanday yozuvsiz (caption'siz) toza holda tez tashlab beradi
            await message.answer_video(
                video=video_file, 
                request_timeout=120
            )
        else:
            await message.answer("❌ Xatolik: Videoni yuklab bo'lmadi!")

    except Exception as e:
        print(f"Xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi!")

    finally:
        if os.path.exists(user_folder):
            shutil.rmtree(user_folder, ignore_errors=True)


async def main():
    print("🚀 Tezkor bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
