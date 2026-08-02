import os
import shutil
import asyncio

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
        "Salom! Bot ishga tushdi. 🤝\n"
        "Faqat YouTube Shorts linklarini yuboring!"
    )
    await message.answer(text)


async def download_video(url: str, folder: str):
    """YouTube Shorts videolarini muammosiz yuklab olish funksiyasi"""
    try:
        ydl_opts = {
            # Xatolik bermaydigan universal format sozlamasi
            'format': 'best/worst',
            'outtmpl': os.path.join(folder, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
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
    url = message.text.strip()
    
    # Faqat YouTube va Shorts havolalarini tekshirish
    if not url.startswith(("http://", "https://")) or ("youtube.com" not in url and "youtu.be" not in url):
        await message.answer("❌ Iltimos faqat YouTube Shorts linkini yuboring!")
        return

    status = await message.answer("⏳")

    user_folder = os.path.join(DOWNLOAD_DIR, str(message.from_user.id))
    os.makedirs(user_folder, exist_ok=True)

    try:
        video_path = await download_video(url, user_folder)

        if video_path and os.path.exists(video_path):
            video_file = FSInputFile(video_path)
            
            final_caption = "📥 YouTube Shorts yuklab olindi ✅"

            await message.answer_video(
                video=video_file, 
                caption=final_caption, 
                request_timeout=120
            )
            
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=status.message_id)
            except:
                pass
            print("✅ Shorts video muvaffaqiyatli yuborildi!")
        else:
            await status.edit_text("❌ Videoni yuklab bo'lmadi. Linkni tekshirib qayta yuboring!")

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
    print("🚀 YouTube Shorts bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
