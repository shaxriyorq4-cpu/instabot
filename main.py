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
    await message.answer("Salom! Link yuboring, chaqmoq tezligida tashlab beraman. ⚡️")


async def get_video_url(url: str):
    """Orqa fonda yt-dlp orqali videoni qidirish funksiyasi"""
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('url')
    except:
        return None


@dp.message()
async def link_handler(message: types.Message):
    url = message.text.strip()
    
    if not url.startswith(("http://", "https://")):
        await message.answer("❌ To'g'ri link yuboring.")
        return

    # Xabarni chiqaramiz
    status = await message.answer("⚡ 1...")
    
    # Videoni orqa fonda qidirishni boshlab yuboramiz (parallel jarayon)
    task = asyncio.create_task(get_video_url(url))

    # 1 sekund kutamiz
    await asyncio.sleep(1.0)
    try:
        await status.edit_text("⚡ 2...")
    except:
        pass

    # Yana 1 sekund kutamiz
    await asyncio.sleep(1.0)
    try:
        await status.edit_text("⚡ 3...")
    except:
        pass

    # Orqa fondagi qidiruv tugashini kutamiz (agar biroz qolgan bo'lsa)
    direct_url = await task

    try:
        if direct_url:
            # 3 soniya tugashi bilan darhol videoni tashlaymiz
            await message.answer_video(video=direct_url)
            await bot.delete_message(chat_id=message.chat.id, message_id=status.message_id)
            print("✅ 3-soniyada muvaffaqiyatli tashlandi!")
            return
        
        # Agar 1-usul ishlamasa, zaxira yuklash usuli
        status_backup = await message.answer("⏳ Tayyorlanmoqda...")
        user_folder = os.path.join(DOWNLOAD_DIR, str(message.from_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'outtmpl': os.path.join(user_folder, '%(id)s.%(ext)s'),
            'concurrent_fragment_downloads': 5
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        if os.path.exists(filename):
            video_file = FSInputFile(filename)
            await message.answer_video(video=video_file, request_timeout=120)
            await bot.delete_message(chat_id=message.chat.id, message_id=status.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=status_backup.message_id)
            shutil.rmtree(user_folder, ignore_errors=True)
        else:
            await status_backup.edit_text("❌ Video topilmadi.")

    except Exception as e:
        print("❌ XATOLIK:")
        traceback.print_exc()
        try:
            await status.edit_text("❌ Xatolik yuz berdi.")
        except:
            pass


async def main():
    print("🚀 Ultratezkor bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
