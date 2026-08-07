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
    await message.answer("Salom! Menga Instagram rasm yoki karusel havolasini yuboring.")

@dp.message(F.text.contains("instagram.com"))
async def download_insta_photos(message: types.Message):
    url = message.text.split("?")[0]
    msg = await message.answer("⏳ Rasmlar yuklanmoqda...")

    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s_%(autonumber)s.%(ext)s'),
        'quiet': True,
        'extract_flat': True, # Videolarni emas, faqat havoladagi elementlarni yig'ish uchun
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
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(str(base_id)):
                file_path = os.path.join(DOWNLOAD_DIR, f)
                if f.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    media_photos.append(InputMediaPhoto(media=FSInputFile(file_path)))

        if media_photos:
            await message.answer_media_group(media=media_photos[:10])
        else:
            await message.answer("❌ Bu havoladan rasm topib bo'lmadi.")

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
        await message.answer("❌ Xatolik yuz berdi. Iltimos boshqa havola yuborib ko'ring.")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
