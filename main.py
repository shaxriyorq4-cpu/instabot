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
    await message.answer("Salom! Link yuboring, video tayyor bo'lishi bilan darhol tashlab beraman. ⚡️")


async def download_video_background(url: str, folder: str):
    """Videoni orqa fonda maksimal tezlikda yuklab olish"""
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'outtmpl': os.path.join(folder, '%(id)s.%(ext)s'),
            'concurrent_fragment_downloads': 5
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if os.path.exists(filename):
                return filename
    except Exception as e:
        print(f"Yuklashda xato: {e}")
    return None


@dp.message()
async def link_handler(message: types.Message):
    url = message.text.strip()
    
    if not url.startswith(("http://", "https://")):
        await message.answer("❌ To'g'ri link yuboring.")
        return

    user_folder = os.path.join(DOWNLOAD_DIR, str(message.from_user.id))
    os.makedirs(user_folder, exist_ok=True)

    # 1. Videoni orqa fonda darhol yuklashni boshlaymiz
    download_task = asyncio.create_task(download_video_background(url, user_folder))

    # 2. Sanoq xabarini chiqaramiz
    status = await message.answer("⚡ 1...")

    # Sanoqni va videoning tayyor bo'lishini bir vaqtda kuzatamiz (kim birinchi bo'lsa)
    # Ya'ni video tezroq yuklansa, darhol tashlanadi va sanoq to'xtatiladi.
    
    # "2" ga o'tamiz
    await asyncio.sleep(0.4)
    if download_task.done():
        video_path = await download_task
        await send_video_and_cleanup(message, status, video_path, user_folder)
        return
    try:
        await status.edit_text("⚡ 2...")
    except:
        pass

    # "3" ga o'tamiz
    await asyncio.sleep(0.4)
    if download_task.done():
        video_path = await download_task
        await send_video_and_cleanup(message, status, video_path, user_folder)
        return
    try:
        await status.edit_text("⚡ 3...")
    except:
        pass

    # Agar hali ham yuklanayotgan bo'lsa, oxirigacha kutamiz
    video_path = await download_task
    await send_video_and_cleanup(message, status, video_path, user_folder)


async def send_video_and_cleanup(message, status, video_path, user_folder):
    """Videoni yuborish va papkani tozalash yordamchi funksiyasi"""
    try:
        if video_path and os.path.exists(video_path):
            video_file = FSInputFile(video_path)
            await message.answer_video(video=video_file, request_timeout=120)
            
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=status.message_id)
            except:
                pass
            print("✅ Video tayyor bo'lishi bilan darhol tashlandi!")
        else:
            await status.edit_text("❌ Video topilmadi yoki yuklab bo'lmadi.")
    except Exception as e:
        print(f"Yuborishda xato: {e}")
    finally:
        if os.path.exists(user_folder):
            shutil.rmtree(user_folder, ignore_errors=True)


async def main():
    print("🚀 Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
