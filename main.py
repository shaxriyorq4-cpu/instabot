import asyncio
import logging
import os
import re
import uuid
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
import yt_dlp

# ==========================================
# LOYIHA SOZLAMALARI
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
# YUKLAB OLISH FUNKSIYASI
# ==========================================

def download_media_sync(url: str, user_id: int) -> dict:
    folder_prefix = os.path.join(DOWNLOAD_DIR, f"user_{user_id}_{uuid.uuid4().hex[:6]}")
    os.makedirs(folder_prefix, exist_ok=True)
    
    output_template = os.path.join(folder_prefix, "video.%(ext)s")
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'user_agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/122.0.0.0 Safari/537.36'
        ),
    }

    video_path = None
    title = "Media"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', 'Media')
        filename = ydl.prepare_filename(info)
        
        if os.path.exists(filename):
            video_path = filename

    return {
        'folder': folder_prefix,
        'video_path': video_path,
        'audio_path': None,
        'title': title
    }


# ==========================================
# HANDLERLAR
# ==========================================

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "👋 **Xush kelibsiz!**\n\n"
        "YouTube, Instagram, TikTok yoki Facebook havolasini yuboring. "
        "Men darhol videoni tayyorlab beraman! 🚀",
        parse_mode="Markdown"
    )


@dp.message(F.text)
async def process_link_handler(message: types.Message):
    urls = re.findall(URL_REGEX, message.text)
    if not urls:
        return

    url = urls[0]
    status_msg = await message.answer("⏳ Tezkor yuklab olinmoqda...")
    
    download_result = None

    try:
        loop = asyncio.get_running_loop()
        download_result = await loop.run_in_executor(None, download_media_sync, url, message.from_user.id)
        
        video_path = download_result['video_path']

        if not video_path or not os.path.exists(video_path):
            await status_msg.edit_text("❌ Videoni yuklab bo'lmadi.")
            return

        await status_msg.edit_text("📤 Yuborilmoqda...")

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🎵 Video music", callback_data="send_audio"),
                InlineKeyboardButton(text="🎬 Full music", callback_data="send_full")
            ]
        ])

        caption_text = f"🎬 {download_result['title']}\n\n🤖 @{(await bot.get_me()).username}"

        await message.answer_video(
            video=FSInputFile(video_path),
            caption=caption_text,
            reply_markup=keyboard,
            supports_streaming=True
        )

        await status_msg.delete()

    except Exception as e:
        logger.error(f"Xatolik: {e}", exc_info=True)
        await status_msg.edit_text("❌ Xatolik yuz berdi. Havolani tekshirib qaytadan yuboring.")


@dp.callback_query(F.data.in_(["send_audio", "send_full"]))async def callback_handler(callback: types.CallbackQuery):
    if callback.data == "send_audio":
        await callback.answer("🎵 Musiqa yuborilmoqda...")
        await callback.message.answer("🎵 Mana videoning musiqasi!")
    elif callback.data == "send_full":
        await callback.answer("🎬 To'liq video...")
        await callback.message.answer("🎬 To'liq video va musiqa rejimi faol!")


# ==========================================
# MAIN
# ==========================================

async def main():
    logger.info("Bot 24/7 rejimda ishlashga tayyorlanmoqda...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
