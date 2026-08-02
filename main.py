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
    await message.answer("Salom! instadown_v2_botiga xush kelibsiz. 🤝ishni boshlaymizmi!")


async def download_video(url: str, folder: str):
    """Videoni tezkor yuklab olish va oddiy mp4 formatga keltirish"""
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
        await message.answer("❌ Iltimos linkni tekshirib qayta yuboring.")
        return

    # Qum soat quyamiz
    status = await message.answer("⏳")

    user_folder = os.path.join(DOWNLOAD_DIR, str(message.from_user.id))
    os.makedirs(user_folder, exist_ok=True)

    try:
        # Videoni yuklab olamiz
        video_path = await download_video(url, user_folder)

        if video_path and os.path.exists(video_path):
            # FSInputFile orqali yuborsak, u HECH QACHON GIF bo'lmaydi, toza video bo'ladi
            video_file = FSInputFile(video_path)
            await message.answer_video(video=video_file, request_timeout=120)
            
            # Qum soatni o'chiramiz
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=status.message_id)
            except:
                pass
            print("✅ Video muvaffaqiyatli yuborildi!")
        else:
            await status.edit_text("❌ Videoni topib bo'lmadi.")

    except Exception as e:
        print(f"Xatolik: {e}")
        try:
            await status.edit_text("❌ Xatolik yuz berdi.")
        except:
            pass

    finally:
        if os.path.exists(user_folder):
            shutil.rmtree(user_folder, ignore_errors=True)


async def main():
    print("🚀 Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
