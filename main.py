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
    await message.answer("Salom! Link yuboring, 3 deganda darhol tashlab beraman. ⚡️")


async def get_video_url(url: str):
    """Orqa fonda yt-dlp orqali videoni qidirish"""
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

    # 1. Havola kelishi bilan birinchi navbatda orqa fonda videoni qidirishni boshlaymiz
    task = asyncio.create_task(get_video_url(url))

    # 2. Shu zahotiyoq "1" ni chiqaramiz
    status = await message.answer("⚡ 1...")
    
    # 0.4 sekund kutib "2" ni chiqaramiz (vaqtni o'zingizga moslab biroz qisqartirdik)
    await asyncio.sleep(0.4)
    try:
        await status.edit_text("⚡ 2...")
    except:
        pass

    # Yana 0.4 sekund kutib "3" ni chiqaramiz
    await asyncio.sleep(0.4)
    try:
        await status.edit_text("⚡ 3...")
    except:
        pass

    # 3 chiqishi bilan orqa fondagi qidiruv natijasini olamiz (u allaqachon tayyor bo'lgan bo'ladi)
    direct_url = await task

    try:
        if direct_url:
            # 3 chiqishi bilan darhol videoni tashlaymiz
            await message.answer_video(video=direct_url)
            await bot.delete_message(chat_id=message.chat.id, message_id=status.message_id)
            print("✅ 3 deganda tashlandi!")
            return
        
        # Agar to'g'ridan-to'g'ri link o'xshamasa (zaxira yuklash)
        status_backup = await message.answer("⏳ Yuklanmoqda...")
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
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=status_backup.message_id)
            except:
                pass
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
    print("🚀 Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
