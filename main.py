import os
import shutil
import asyncio
import traceback

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile

import yt_dlp


TOKEN = "8915219066:AAGSCkzvFImev5HLBdOMqv-q8CWjraGnsHg"

bot = Bot(token=TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Salom! Instagram Reel yoki YouTube linkini yuboring.")


async def download_video_ytdlp(url: str, folder: str):
    try:
        print(f"🔍 [yt-dlp] Video yuklanmoqda: {url}")
        
        ydl_opts = {
            'outtmpl': os.path.join(folder, '%(id)s.%(ext)s'),
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Agar kengaytmali fayl mavjud bo'lsa
            if os.path.exists(filename):
                print(f"✅ [yt-dlp] Muvaffaqiyatli yuklandi: {filename}")
                return filename

        # Papka ichidan qidirib topish
        for file in os.listdir(folder):
            if file.lower().endswith(('.mp4', '.mkv', '.webm')):
                file_path = os.path.abspath(os.path.join(folder, file))
                print(f"✅ [yt-dlp] Topilgan fayl: {file_path}")
                return file_path

    except Exception as e:
        print(f"❌ XATOLIK [yt-dlp]:")
        traceback.print_exc()

    return None


@dp.message()
async def link_handler(message: types.Message):
    url = message.text.strip()
    
    if not url.startswith(("http://", "https://")):
        await message.answer("❌ To'g'ri link yuboring.")
        return

    status = await message.answer("⏳ Video yuklanmoqda...")

    user_folder = os.path.join(DOWNLOAD_DIR, str(message.from_user.id))
    os.makedirs(user_folder, exist_ok=True)

    try:
        video_path = await download_video_ytdlp(url, user_folder)

        if video_path and os.path.exists(video_path):
            print(f"📤 Telegramga yuborilmoqda: {video_path}")
            
            file_size = os.path.getsize(video_path)
            if file_size > 50 * 1024 * 1024:
                await status.edit_text("❌ Video hajmi 50 MB dan katta!")
                return

            video_file = FSInputFile(video_path)
            await message.answer_video(video=video_file, request_timeout=120)
            
            print("✅ Telegramga yuborildi!")
            await bot.delete_message(chat_id=message.chat.id, message_id=status.message_id)
        else:
            await status.edit_text("❌ Xatolik: Video fayl topilmadi.")

    except Exception as e:
        print(f"❌ KRITIK XATO:")
        traceback.print_exc()
        await status.edit_text(f"❌ Xato: {e}")

    finally:
        if os.path.exists(user_folder):
            shutil.rmtree(user_folder, ignore_errors=True)


async def main():
    print("🤖 Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
