import os
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, InputMediaPhoto
import yt_dlp

TOKEN = "8763107587:AAEK33xTw8yoexp7zCG0aNphcHiDUKECMks"

bot = Bot(token=TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def is_supported_url(text: str) -> bool:
    platforms = ["instagram.com", "tiktok.com", "youtube.com", "youtu.be"]
    return any(p in text for p in platforms)

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "Salom! 👋\n"
        "Menga **Instagram** (Reels, Post, Karusel, Story), **YouTube** yoki **TikTok** havolasini yuboring.\n"
        "Men sizga kontentni va uning **musiqasini** chiqarib beraman!"
    )

@dp.message(F.text & ~F.text.startswith("/"))
async def download_content(message: types.Message):
    url = message.text.strip()
    
    if not is_supported_url(url):
        await message.answer("❌ Iltimos, faqat Instagram, YouTube yoki TikTok havolasini yuboring.")
        return

    processing_msg = await message.answer("⏳ Yuklab olinmoqda, biroz kuting...")

    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s_%(autonumber)s.%(ext)s'),
        'format': 'best/bestvideo+bestaudio',
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

        if not downloaded_files:
            await message.answer("❌ Afsuski, bu havoladan kontent topib bo'lmadi.")
            return

        audio_path = os.path.join(DOWNLOAD_DIR, f"{base_id}.mp3")
        audio_opts = {
            'outtmpl': audio_path.replace('.mp3', '.%(ext)s'),
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
            'quiet': True,
            'ignoreerrors': True,
        }
        if os.path.exists('cookies.txt'):
            audio_opts['cookiefile'] = 'cookies.txt'
        
        def extract_audio():
            try:
                with yt_dlp.YoutubeDL(audio_opts) as ydl:
                    ydl.extract_info(url, download=True)
            except:
                pass

        await loop.run_in_executor(None, extract_audio)

        has_audio = os.path.exists(audio_path)
        keyboard = None
        if has_audio:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🎵 Musiqasi", callback_data=f"audio_{base_id}")]
                ]
            )

        media_photos = []
        for file_path in downloaded_files:
            if file_path.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                media_photos.append(InputMediaPhoto(media=FSInputFile(file_path)))

        if len(media_photos) > 1:
            await message.answer_media_group(media=media_photos)
            if has_audio:
                await message.answer("👆 Karusel rasmlari yuqorida.", reply_markup=keyboard)
        elif len(media_photos) == 1:
            await message.answer_photo(photo=FSInputFile(downloaded_files[0]), reply_markup=keyboard)
        else:
            for file_path in downloaded_files:
                if file_path.endswith(('.mp4', '.mkv', '.webm', '.mov', '.m4v', '.avi')):
                    await message.answer_video(video=FSInputFile(file_path), reply_markup=keyboard)
                    break

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
        await message.answer("❌ Xatolik yuz berdi. Havola yopiq yoki yaroqsiz bo'lishi mumkin.")

@dp.callback_query(F.data.startswith("audio_"))
async def send_audio_callback(callback: types.CallbackQuery):
    try:
        await callback.answer("Musiqa yuborilmoqda...")
    except:
        pass

    base_id = callback.data.split("_")[1]
    audio_path = os.path.join(DOWNLOAD_DIR, f"{base_id}.mp3")

    if os.path.exists(audio_path):
        await callback.message.answer_audio(audio=FSInputFile(audio_path), caption="🎵 Musiqa tayyor!")
        try:
            os.remove(audio_path)
        except:
            pass
    else:
        await callback.message.answer("❌ Kechirasiz, bu musiqaning vaqti o'tib ketgan yoki topilmadi.")

async def main():
    print("Bot ishga tushdi...")
    # Eski so'rovlarni tozalash (ConflictError'ni oldini olish uchun)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
