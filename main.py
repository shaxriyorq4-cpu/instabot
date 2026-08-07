import os
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, InputMediaPhoto
import yt_dlp

TOKEN = "8798843673:AAHDW5utYbz8g12P8KBRqbKdecYC0Ki2rfo"

bot = Bot(token=TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Salom! Menga Instagram post yoki karusel havolasini yuboring, men ularni yuklab beraman.")

@dp.message(F.text.contains("instagram.com"))
async def download_insta(message: types.Message):
    url = message.text.split("?")[0]
    msg = await message.answer("⏳ Yuklanmoqda...")

    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s_%(autonumber)s.%(ext)s'),
        'quiet': True,
        'format': 'best/bestvideo+bestaudio',
        'ignoreerrors': True, # Xatolikka uchragan qismlarini tashlab o'tib ketish uchun
    }
    
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        def run_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=True)

        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, run_dl)
        
        if not info:
            raise Exception("Ma'lumot topilmadi.")

        base_id = info.get('id', 'media')
        
        media_photos = []
        video_file = None

        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(str(base_id)):
                file_path = os.path.join(DOWNLOAD_DIR, f)
                if f.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    media_photos.append(InputMediaPhoto(media=FSInputFile(file_path)))
                elif f.endswith(('.mp4', '.mov', '.mkv', '.webm')):
                    video_file = file_path

        if media_photos:
            await message.answer_media_group(media=media_photos[:10])
        elif video_file:
            await message.answer_video(video=FSInputFile(video_file))
        else:
            await message.answer("❌ Kontent topilmadi yoki havola yopiq.")

        # Fayllarni tozalash
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(str(base_id)):
                try:
                    os.remove(os.path.join(DOWNLOAD_DIR, f))
                except:
                    pass
        
        try:
            await bot.delete_message(message.chat.id, msg.message_id)
        except:
            pass

    except Exception as e:
        try:
            await bot.delete_message(message.chat.id, msg.message_id)
        except:
            pass
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
