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
    # 1. Start bosgandagi xabar
    text = (
        "Salom! @instadown_v2_bot ga xush kelibsiz. 🤝\n"
        "ishni boshlaymizmi!"
    )
    await message.answer(text)


async def download_video(url: str, folder: str):
    """Videoni va uning original matnini (caption) yuklab olish"""
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
            'outtmpl': os.path.join(folder, '%(id)s.%(ext)s'),
            'concurrent_fragment_downloads': 5
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # Instagram postining original matnini olamiz
            original_caption = info.get('description', '')
            if os.path.exists(filename):
                return filename, original_caption
    except Exception as e:
        print(f"Yuklashda xato: {e}")
    return None, None


@dp.message()
async def link_handler(message: types.Message):
    url = message.text.strip()
    
    # Agar xabar link bilan boshlanmasa
    if not url.startswith(("http://", "https://")):
        # 2. Link bo'lmasa yoziladigan xabar
        await message.answer("❌ Iltimos linkni tekshirib qayta yuboring!")
        return

    # 3. Qum soat aylanib turishi uchun xabar
    status = await message.answer("⏳")

    user_folder = os.path.join(DOWNLOAD_DIR, str(message.from_user.id))
    os.makedirs(user_folder, exist_ok=True)

    try:
        # Videoni va uning matnini yuklab olamiz
        video_path, original_caption = await download_video(url, user_folder)

        if video_path and os.path.exists(video_path):
            video_file = FSInputFile(video_path)
            
            # 4. Videoning o'zi bilan birga original matni va "Marxamat buyurtmangiz ✅" yozuvi
            final_caption = f"Marxamat buyurtmangiz ✅"
            if original_caption:
                final_caption = f"{original_caption}\n\nMarxamat buyurtmangiz ✅"

            await message.answer_video(
                video=video_file, 
                caption=final_caption, 
                request_timeout=120
            )
            
            # Qum soatni o'chiramiz
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=status.message_id)
            except:
                pass
            print("✅ Video muvaffaqiyatli yuborildi!")
        else:
            # 5. Linkda xatolik bo'lsa yoki video topilmasa
            await status.edit_text("❌ linkda xatolik bor Iltimos linkni tekshirib qayta yuboring!")

    except Exception as e:
        print(f"Xatolik: {e}")
        try:
            # 5. Har qanday xatolik holatida ham
            await status.edit_text("❌ linkda xatolik bor Iltimos linkni tekshirib qayta yuboring!")
        except:
            pass

    finally:
        if os.path.exists(user_folder):
            shutil.rmtree(user_folder, ignore_errors=True)


async def main():
    print("🚀 Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
