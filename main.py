import os
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, InputMediaPhoto
import yt_dlp

TOKEN = "8763107587:AAEK33xTw8yoexp7zCG0aNphcHiDUKECMks"

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
    url = message.text.split("?")[0] # Havolani tozalash
    msg = await message.answer("⏳ Yuklanmoqda...")

    # yt-dlp sozlamalari
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s_%(autonumber)s.%(ext)s'),
        'quiet': True,
        'format': 'best',
    }

    try:
        def run_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=True)

        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, run_dl)
        
        base_id = info.get('id')
        
        # Yuklangan fayllarni yig'ish
        media_group = []
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(str(base_id)) and f.endswith(('.jpg', '.jpeg', '.png')):
                media_group.append(InputMediaPhoto(media=FSInputFile(os.path.join(DOWNLOAD_DIR, f))))
        
        # Javob qaytarish
        if media_group:
            # Telegram 10 ta rasmga ruxsat beradi
            await message.answer_media_group(media=media_group[:10])
        else:
            await message.answer("❌ Rasm topilmadi. Havola ochiqligini tekshiring.")

        # Tozalash
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(str(base_id)):
                try: os.remove(os.path.join(DOWNLOAD_DIR, f))
                except: pass
        
        await bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        await message.answer(f"Xatolik: {str(e)}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
