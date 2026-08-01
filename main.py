import asyncio
import logging
import os
import re
import aiohttp
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

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Salom! 👋\n\n"
        "Instagram'dan istalgan video, rasm, reels, story va postlarni yuboring!\n\n"
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

    media_items = [] 
    error_message = None

    # 1-usul: Cobalt API orqali urinib ko'rish
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://co.wuk.sh/api/json",
                json={
                    "url": url,
                    "vQuality": "max",
                    "isAudioMuted": False,
                },
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            ) as resp:
                res = await resp.json()
                status = res.get("status")
                if status in ["stream", "redirect"]:
                    media_items.append((res.get("url"), "video"))
                elif status == "picker":
                    items = res.get("picker")
                    if items:
                        for item in items:
                            m_type = "photo" if item.get("type") == "photo" else "video"
                            media_items.append((item.get("url"), m_type))
    except Exception as e:
        logging.error(f"Cobalt API xatosi: {e}")

    # 2-usul: Agar Cobalt ololmasa, yt-dlp orqali cookies bilan tortish
    if not media_items:
        try:
            ydl_opts = {
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s_%(autonumber)s.%(ext)s'),
                'format': 'best/bestvideo+bestaudio/best',
                'cookiefile': 'cookies.txt',
                'ignoreerrors': True,
            }
            
            def download():
                files = []
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if not info:
                        return []
                    if 'entries' in info:
                        for entry in info['entries']:
                            if entry:
                                f = ydl.prepare_filename(entry)
                                if os.path.exists(f):
                                    files.append(f)
                    else:
                        f = ydl.prepare_filename(info)
                        if os.path.exists(f):
                            files.append(f)
                return files

            downloaded_files = await asyncio.to_thread(download)
            for f in downloaded_files:
                m_type = "photo" if f.endswith(('.jpg', '.jpeg', '.png', '.webp')) else "video"
                media_items.append((f, m_type, True)) 
        except Exception as e:
            error_message = str(e)
            logging.error(f"yt-dlp xatosi: {e}")

    # Natijani foydalanuvchiga yuborish
    if media_items:
        try:
            for item in media_items:
                if len(item) == 3: # Local file (yt-dlp)
                    file_path, m_type, _ = item
                    media_file = types.FSInputFile(file_path)
                    if m_type == "photo":
                        await message.answer_photo(photo=media_file)
                    else:
                        await message.answer_video(video=media_file)
                    try:
                        os.remove(file_path)
                    except:
                        pass
                else: # URL (Cobalt)
                    m_url, m_type = item
                    if m_type == "photo":
                        await message.answer_photo(photo=m_url)
                    else:
                        await message.answer_video(video=m_url)
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
