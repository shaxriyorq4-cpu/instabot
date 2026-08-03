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
        "Salom! YouTube va Shorts yuklash boti ishga tushdi. 🤝\n"
        "Videolar havolasini yuboring!"
    )
    await message.answer(text)


async def download_video(url: str, folder: str):
    """Cookie xatolarini chetlab o'tib, yuqori sifatli videoni tez yuklash"""
    try:
        ydl_opts = {
            # Yuqori sifatli tayyor bitta faylni olish (GVS PO token xatosiga uchramaslik uchun)
            'format': 'best[height<=1080]/best',
            'outtmpl': os.path.join(folder, '%(id)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'remote_components': ['ejs:github'],
            # Agar cookies eskirgan bo'lsa xato bermasligi uchun uni shartli qo'shamiz
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            'extractor_args': {
                'youtube': {
                    # PO token talab qiladigan muammoli mijozlarni olib tashlaymiz
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
        print("\n--- YUKLASHDA XATOLIK YUZ BERDI ---")
        print(str(e))
        traceback.print_exc()
        print("------------------------------------\n")
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
            
            final_caption = "📥 YouTube videosi yuklab olindi ✅"

            await message.answer_video(
                video=video_file, 
                caption=final_caption, 
                request_timeout=120
            )
            
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=status.message_id)
            except:
                pass
            print("✅ Video muvaffaqiyatli yuborildi!")
        else:
            await status.edit_text("❌ Videoni yuklab bo'lmadi. Railway Logs ni tekshiring!")

    except Exception as e:
        print(f"Handler xatoligi: {e}")
        try:
            await status.edit_text("❌ Kutilmagan xatolik yuz berdi!")
        except:
            pass

    finally:
        if os.path.exists(user_folder):
            shutil.rmtree(user_folder, ignore_errors=True)


async def main():
    print("🚀 YouTube tezkor bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
