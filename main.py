import os
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
import yt_dlp

TOKEN = "8915219066:AAG1AVjvXJXhPPvTwhMRDkdZq4gpuM3MTSE"

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
        "Menga **Instagram**, **YouTube** yoki **TikTok** havolasini yuboring.\n"
        "Men sizga videoni va uning **musiqasini** chiqarib beraman!"
    )

@dp.message(F.text & ~F.text.startswith("/"))
async def download_content(message: types.Message):
    url = message.text.strip()
    
    if not is_supported_url(url):
        await message.answer("❌ Iltimos, faqat Instagram, YouTube yoki TikTok havolasini yuboring.")
        return

    processing_msg = await message.answer("⏳ Kontent yuklab olinmoqda, biroz kuting...")

    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
        'format': 'best/bestvideo+bestaudio',
        'noplaylist': True,
        'quiet': True,
        'ignoreerrors': True,
    }

    try:
        def extract_info():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return info

        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, extract_info)

        if not info:
            raise Exception("Ma'lumot topilmadi")

        file_path = yt_dlp.YoutubeDL(ydl_opts).prepare_filename(info)
        base_id = info.get('id', 'audio')

        audio_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, f"{base_id}.%(ext)s"),
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
        }

        def extract_audio():
            with yt_dlp.YoutubeDL(audio_opts) as ydl:
                ydl.extract_info(url, download=True)

        await loop.run_in_executor(None, extract_audio)

        await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🎵 Musiqasi", callback_data=f"audio_{base_id}")]
            ]
        )

        if os.path.exists(file_path):
            if file_path.endswith(('.mp4', '.mkv', '.webm', '.mov', '.m4v')):
                await message.answer_video(video=FSInputFile(file_path), reply_markup=keyboard)
            elif file_path.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                await message.answer_photo(photo=FSInputFile(file_path), reply_markup=keyboard)
            else:
                await message.answer_document(document=FSInputFile(file_path), reply_markup=keyboard)
        else:
            await message.answer("❌ Faylni yuborishda xatolik yuz berdi.")

        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
        except:
            pass
        await message.answer("❌ Kechirasiz, bu havoladan videoni yuklab bo'lmadi. Havola yopiq yoki yaroqsiz bo'lishi mumkin.")

@dp.callback_query(F.data.startswith("audio_"))
async def send_audio_callback(callback: types.CallbackQuery):
    base_id = callback.data.split("_")[1]
    audio_path = os.path.join(DOWNLOAD_DIR, f"{base_id}.mp3")

    if os.path.exists(audio_path):
        await callback.message.answer_audio(audio=FSInputFile(audio_path), caption="🎵 Musiqa tayyor!")
        await callback.answer()
        try:
            os.remove(audio_path)
        except:
            pass
    else:
        await callback.answer("❌ Kechirasiz, bu musiqani topib bo'lmadi.", show_alert=True)

async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
