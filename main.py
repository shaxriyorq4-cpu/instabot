import os
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, InputMediaPhoto
import yt_dlp

TOKEN = "8798843673:AAHUPeLpIZgtWLSl05GPs1HJmnpXuLdMHGc"

bot = Bot(token=TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "Salom! 👋\n"
        "Menga Instagram post (karusel yoki rasm) havolasini yuboring, men rasmlarini yuklab beraman."
    )

@dp.message(F.text & ~F.text.startswith("/"))
async def download_photos(message: types.Message):
    url = message.text.strip()
    
    if "instagram.com" not in url:
        await message.answer("❌ Iltimos, faqat Instagram havolasini yuboring.")
        return

    processing_msg = await message.answer("⏳ Ma'lumotlar yuklab olinmoqda, biroz kuting...")

    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s_%(autonumber)s.%(ext)s'),
        'noplaylist': False,
        'quiet': True,
        'ignoreerrors': True,
    }
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        def extract_info():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return info

        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, extract_info)

        if not info:
            raise Exception("Ma'lumot topilmadi")

        base_id = info.get('id', 'media')

        downloaded_files = []
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(str(base_id)):
                downloaded_files.append(os.path.join(DOWNLOAD_DIR, f))

        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
        except:
            pass

        media_photos = []
        for file_path in downloaded_files:
            if file_path.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                media_photos.append(InputMediaPhoto(media=FSInputFile(file_path)))

        if len(media_photos) > 1:
            await message.answer_media_group(media=media_photos)
        elif len(media_photos) == 1:
            await message.answer_photo(photo=FSInputFile(downloaded_files[0]))
        else:
            await message.answer("❌ Bu havoladan mos formatdagi rasm topilmadi.")

        for file_path in downloaded_files:
            try:
                os.remove(file_path)
            except:
                pass

    except Exception as e:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
        except:
            pass
        await message.answer("❌ Xatolik yuz berdi. Havola yopiq, o'chirilgan yoki yaroqsiz bo'lishi mumkin.")

async def main():
    print("Bot ishga tushdi...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, handle_signals=False)

if __name__ == "__main__":
    asyncio.run(main())
