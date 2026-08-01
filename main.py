import asyncio
import logging
import os
import re
import instaloader
import yt_dlp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = "8915219066:AAEapW0Id_nw6Ex1hZsm8tcTxmR4x8k-Zag"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

URL_REGEX = re.compile(
    r'http[s]?://(?:[a-zA-Z0-9$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
)

L = instaloader.Instaloader(
    download_videos=True,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False
)

# Cookies fayli orqali instaloader'ga kirish
try:
    if os.path.exists("cookies.txt"):
        L.load_session_from_file("", "cookies.txt")
except Exception as e:
    logging.error(f"Instaloader cookies yuklashda xato: {e}")

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Salom! 👋\n\n"
        "Instagram'dan istalgan video, rasm, reels, story va karusel postlarni yuboring!\n\n"
        "🚀 Havolani yuboring!"
    )

@dp.message()
async def process_link_handler(message: types.Message):
    text = message.text
    match = URL_REGEX.search(text)
    
    if not match:
        return

    url = match.group(0)
    processing_msg = await message.answer("⏳ Yuklab olinmoqda, iltimos kuting...")

    downloaded_files = []
    error_message = None

    try:
        def download_with_instaloader():
            files = []
            # Shortcode ni havoladan ajratib olish (/p/SHORTCODE/ yoki /reel/SHORTCODE/)
            shortcode_match = re.search(r'/(?:p|reel|tv)/([^/?#&]+)', url)
            if not shortcode_match:
                return []
            
            shortcode = shortcode_match.group(1)
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            
            # Vaqtinchalik papka
            target_dir = os.path.join(DOWNLOAD_DIR, shortcode)
            os.makedirs(target_dir, exist_ok=True)
            
            L.download_post(post, target=target_dir)
            
            # Yuklangan fayllarni yig'ish
            for f in os.listdir(target_dir):
                if f.endswith(('.jpg', '.jpeg', '.png', '.mp4')):
                    files.append(os.path.join(target_dir, f))
            return files

        downloaded_files = await asyncio.to_thread(download_with_instaloader)
    except Exception as e:
        error_message = str(e)
        logging.error(f"Instaloader xatosi: {e}")

    # Agar instaloader ololmasa, yt-dlp zaxira sifatida urinib ko'radi
    if not downloaded_files:
        try:
            ydl_opts = {
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s_%(autonumber)s.%(ext)s'),
                'format': 'best/bestvideo+bestaudio/best',
                'cookiefile': 'cookies.txt',
                'ignoreerrors': True,
            }
            def download_yt():
                files = []
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if not info:
                        return []
                    if 'entries' in info:
                        for entry in info['entries']:
                            if entry:
                                f = ydl.prepare_filename(entry)
                                if os.path.exists(f): files.append(f)
                    else:
                        f = ydl.prepare_filename(info)
                        if os.path.exists(f): files.append(f)
                return files
            downloaded_files = await asyncio.to_thread(download_yt)
        except Exception as e:
            if not error_message:
                error_message = str(e)

    if downloaded_files:
        try:
            for file_path in downloaded_files:
                if file_path.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    media_file = types.FSInputFile(file_path)
                    await message.answer_photo(photo=media_file)
                elif file_path.endswith(('.mp4', '.mov', '.mkv', '.webm')):
                    media_file = types.FSInputFile(file_path)
                    await message.answer_video(video=media_file)
            
            # Tozalash
            for file_path in downloaded_files:
                try:
                    os.remove(file_path)
                except:
                    pass
        except Exception as e:
            await message.answer(f"❌ Faylni yuborishda xatolik: {e}")
    else:
        if error_message:
            await message.answer(f"❌ Xatolik tafsiloti:\n<code>{error_message}</code>", parse_mode="HTML")
        else:
            await message.answer("❌ Kechirasiz, bu havoladan ma'lumot olib bo'lmadi.")

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
    except Exception:
        pass

async def main():
    logging.info("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
