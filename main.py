import os
import shutil
import asyncio
import traceback

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile

import instaloader


TOKEN = "8915219066:AAGSCkzvFImev5HLBdOMqv-q8CWjraGnsHg"

bot = Bot(token=TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

L = instaloader.Instaloader(
    download_videos=True,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False
)


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Salom! 👋\n\n"
        "Hozircha faqat **Instagram Reel** havolalarini yuboring, yuklab beraman."
    )


async def download_instagram_reel(url: str, folder: str):
    try:
        if "/reel/" in url:
            shortcode = url.split("/reel/")[1].split("/")[0]
        elif "/p/" in url:
            shortcode = url.split("/p/")[1].split("/")[0]
        else:
            return None

        print(f"🔍 Reel yuklanmoqda. Shortcode: {shortcode}")
        
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=folder)

        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith(".mp4"):
                    file_path = os.path.abspath(os.path.join(root, file))
                    print(f"✅ Topilgan video fayl: {file_path}")
                    return file_path

    except Exception as e:
        print(f"❌ Xatolik yuz berdi:")
        traceback.print_exc()

    return None


@dp.message()
async def link_handler(message: types.Message):
    url = message.text.strip()
    
    if not url.startswith(("http://", "https://")):
        await message.answer("❌ Iltimos, to'g'ri link yuboring.")
        return

    status = await message.answer("⏳ Reel yuklanmoqda...")

    user_folder = os.path.join(DOWNLOAD_DIR, str(message.from_user.id))
    os.makedirs(user_folder, exist_ok=True)

    try:
        video_path = await download_instagram_reel(url, user_folder)

        if video_path and os.path.exists(video_path):
            print(f"📤 Telegramga yuborilmoqda: {video_path}")
            
            file_size = os.path.getsize(video_path)
            print(f"📦 Fayl hajmi: {file_size} bayt")

            if file_size > 50 * 1024 * 1024:
                await status.edit_text("❌ Video hajmi 50 MB dan katta!")
                return

            video_file = FSInputFile(video_path)
            
            try:
                await message.answer_video(video=video_file)
                print("✅ Telegramga muvaffaqiyatli yuborildi!")
            except Exception as send_err:
                print(f"❌ Telegramga yuborishda xato: {send_err}")
                await status.edit_text(f"❌ Yuborishda xato: {send_err}")
                return
            
            await bot.delete_message(chat_id=message.chat.id, message_id=status.message_id)
        else:
            await status.edit_text("❌ Video topilmadi yoki yuklab bo'lmadi.")

    except Exception as e:
        print(f"❌ Kritik xato:")
        traceback.print_exc()
        await status.edit_text(f"❌ Xatolik yuz berdi:\n{e}")

    finally:
        if os.path.exists(user_folder):
            shutil.rmtree(user_folder, ignore_errors=True)


async def main():
    print("🤖 Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
