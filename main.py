import asyncio
import logging
import os
import re
import uuid
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InputMediaVideo, InputMediaPhoto
from aiogram.fsm.storage.memory import MemoryStorage
import yt_dlp

# ==========================================
# LOYIHA SOZLAMALARI (CONFIGURATIONS)
# ==========================================

BOT_TOKEN = "8939497082:AAF176bWwpTm4NpTIFaJ6W_0KyhemuKrNNs"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

DOWNLOAD_DIR = "temp_downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

URL_REGEX = r'https?://(?:www\.)?(?:instagram\.com|instagr\.am|youtube\.com|youtu\.be|tiktok\.com|facebook\.com|fb\.watch|twitter\.com|x\.com)/[^\s]+'


# ==========================================
# YUKLAB OLISH FUNKSIYASI (BRAUZER COOKIES BILAN)
# ==========================================

def download_media_sync(url: str, user_id: int) -> dict:
    folder_prefix = os.path.join(DOWNLOAD_DIR, f"user_{user_id}_{uuid.uuid4().hex[:6]}")
    os.makedirs(folder_prefix, exist_ok=True)
    
    output_template = os.path.join(folder_prefix, "%(autonumber)s_%(id)s.%(ext)s")
    
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_template,
        'cookiesfrombrowser': ('chrome',),  # Kompyuterdagi Chrome brauzerdan Instagram akkaunt ruxsatini oladi
        'quiet': True,
        'no_warnings': True,
        'noplaylist': False,
        'user_agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/122.0.0.0 Safari/537.36'
        ),
    }

    files = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        
        if 'entries' in info:
            entries = info['entries']
        else:
            entries = [info]

        for entry in entries:
            if not entry:
                continue
            filename = ydl.prepare_filename(entry)
            
            if os.path.exists(filename):
                files.append({
                    'path': filename,
                    'is_video': filename.endswith(('.mp4', '.mkv', '.webm', '.mov')),
                    'width': entry.get('width'),
                    'height': entry.get('height'),
                    'duration': entry.get('duration')
                })
            else:
                base, _ = os.path.splitext(filename)
                for ext in ['.mp4', '.jpg', '.png', '.webp']:
                    if os.path.exists(base + ext):
                        files.append({
                            'path': base + ext,
                            'is_video': ext == '.mp4',
                            'width': entry.get('width'),
                            'height': entry.get('height'),
                            'duration': entry.get('duration')
                        })
                        break

    return {
        'folder': folder_prefix,
        'files': files,
        'title': info.get('title', 'Media')
    }


# ==========================================
# HANDLERLAR
# ==========================================

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    welcome_text = (
        "👋 **Xush kelibsiz!**\n\n"
        "Men Instagram (Post, Reels, Karusel, Story), TikTok va YouTube'dan videolarni yuklab beraman.\n\n"
        "🚀 Havolani yuboring!"
    )
    await message.answer(welcome_text, parse_mode="Markdown")


@dp.message(F.text)
async def process_link_handler(message: types.Message):
    urls = re.findall(URL_REGEX, message.text)
    if not urls:
        return

    url = urls[0]
    status_msg = await message.answer("⏳ Yuklab olinmoqda...")
    
    download_result = None

    try:
        loop = asyncio.get_running_loop()
        download_result = await loop.run_in_executor(None, download_media_sync, url, message.from_user.id)
        
        files = download_result['files']

        if not files:
            await status_msg.edit_text("❌ Fayllar topilmadi yoki profil yopiq (Private).")
            return

        await status_msg.edit_text("📤 Telegram'ga yuborilmoqda...")

        # SINGLE (Bitta fayl)
        if len(files) == 1:
            item = files[0]
            video_input = FSInputFile(item['path'])
            caption_text = f"🎬 {download_result['title']}\n\n🤖 @{(await bot.get_me()).username}"

            if item['is_video']:
                await message.answer_video(
                    video=video_input,
                    caption=caption_text,
                    width=item['width'],
                    height=item['height'],
                    duration=item['duration'],
                    supports_streaming=True
                )
            else:
                await message.answer_photo(
                    photo=video_input,
                    caption=caption_text
                )

        # MULTIPLE / KARUSEL (Bir nechta fayl)
        else:
            media_group = []
            for idx, item in enumerate(files[:10]):
                file_input = FSInputFile(item['path'])
                caption = f"🎬 {download_result['title']}\n\n🤖 @{(await bot.get_me()).username}" if idx == 0 else ""

                if item['is_video']:
                    media_group.append(InputMediaVideo(
                        media=file_input,
                        caption=caption,
                        width=item['width'],
                        height=item['height'],
                        duration=item['duration']
                    ))
                else:
                    media_group.append(InputMediaPhoto(
                        media=file_input,
                        caption=caption
                    ))

            await message.answer_media_group(media=media_group)

        await status_msg.delete()

    except yt_dlp.utils.DownloadError as de:
        logger.error(f"yt-dlp Download Error: {de}")
        await status_msg.edit_text("❌ Yuklab olishda xatolik! Chrome brauzerida Instagram ochilganiga va akkauntga kirilganiga ishonch hosil qiling.")
    except Exception as e:
        logger.error(f"Kutilmagan xatolik: {e}", exc_info=True)
        await status_msg.edit_text("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
    finally:
        if download_result and 'folder' in download_result and os.path.exists(download_result['folder']):
            try:
                for f in os.listdir(download_result['folder']):
                    try:
                        os.remove(os.path.join(download_result['folder'], f))
                    except:
                        pass
                os.rmdir(download_result['folder'])
            except Exception:
                pass


# ==========================================
# MAIN
# ==========================================

async def main():
    logger.info("Bot polling rejimida ishga tushmoqda...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")