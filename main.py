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
    text = (
        "Salom! @instadown_v2_bot ga xush kelibsiz. 🤝\n"
        "YouTube va Shorts videolarini yuboring!"
    )
    await message.answer(text)


async def download_video(url: str, folder: str):
    """Faqat YouTube va Shorts videolarini ishonchli yuklab olish funksiyasi"""
    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(folder, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            # YouTube bot ekanligini sezmasligi uchun eng yangi mijoz sozlamalari
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'android', 'web'],
                }
            }
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Agar formatlar birlashtirilgan bo'lsa kengaytmasi mp4 bo'ladi
            base, _ = os.path.splitext(filename)
            mp4_filename = base + '.mp4'
            
            if os.path.exists(mp4_filename):
                return mp4_filename
            elif os.path.exists(filename):
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
    url = message.text.strip()
    
    if not url.startswith(("http://", "https://")) or ("youtube.com" not in url and "youtu.be" not in url):
        await message.answer("❌ Iltimos faqat YouTube yoki Shorts linkini yuboring!")
        return

    status = await message.answer("⏳")

    user_folder = os.path.join(DOWNLOAD_DIR, str(message.from_user.id))
    os.makedirs(user_folder, exist_ok=True)

    try:
        video_path = await download_video(url, user_folder)

        if video_path and os.path.exists(video_path):
            video_file = FSInputFile(video_path)
            
            final_caption = "📥@instadown_v2_bot orqali yuklandi      ✅"

            await message.answer_video(
                video=video_file, 
                caption=final_caption, 
                request_timeout=120
            )
            
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=status.message_id)
            except:
                pass
            print("✅ YouTube video muvaffaqiyatli yuborildi!")
        else:
            await status.edit_text("❌ Videoni yuklab bo'lmadi. Linkni yoki YouTube ruxsatlarini tekshiring!")

    except Exception as e:
        print(f"Xatolik: {e}")
        try:
            await status.edit_text("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring!")
        except:
            pass

    finally:
        if os.path.exists(user_folder):
            shutil.rmtree(user_folder, ignore_errors=True)


async def main():
    print("🚀 YouTube bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
