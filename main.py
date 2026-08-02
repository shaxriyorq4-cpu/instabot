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
    await message.answer("Salom! Link yuboring.")


async def download_instagram_reel(url: str, folder: str):
    try:
        if "/reel/" in url:
            shortcode = url.split("/reel/")[1].split("/")[0]
        elif "/p/" in url:
            shortcode = url.split("/p/")[1].split("/")[0]
        else:
            print("❌ XATOLIK [1-QADAM]: Link ichidan reel yoki p topilmadi.")
            return None

        print(f"🔍 [2-QADAM] Shortcode olindi: {shortcode}. Instaloader ishga tushdi...")
        
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=folder)

        print(f"📂 [3-QADAM] Papka tekshirilmoqda: {folder}")
        
        # Papka ichidagi fayllarni to'liq ko'rsatish
        all_files = os.listdir(folder)
        print(f"📄 Papka ichidagi barcha fayllar: {all_files}")

        for file in all_files:
            # Fayl nomi oxiri .mp4 yoki .MP4 bilan tugashini tekshiramiz
            if file.lower().endswith(".mp4"):
                file_path = os.path.abspath(os.path.join(folder, file))
                print(f"✅ [4-QADAM] MP4 fayl muvaffaqiyatli topildi: {file_path}")
                return file_path

        print("❌ XATOLIK [4-QADAM]: Papka ichidan birorta ham .mp4 topilmadi!")

    except Exception as e:
        print(f"❌ XATOLIK [INSTAGRAM BLOCK]:")
        traceback.print_exc()

    return None


@dp.message()
async def link_handler(message: types.Message):
    url = message.text.strip()
    
    if not url.startswith(("http://", "https://")):
        await message.answer("❌ To'g'ri link yuboring.")
        return

    status = await message.answer("⏳ Tekshirilmoqda...")

    user_folder = os.path.join(DOWNLOAD_DIR, str(message.from_user.id))
    os.makedirs(user_folder, exist_ok=True)

    try:
        video_path = await download_instagram_reel(url, user_folder)

        if video_path and os.path.exists(video_path):
            print(f"📤 [5-QADAM] Telegramga yuborilmoqda...")
            
            video_file = FSInputFile(video_path)
            await message.answer_video(video=video_file, request_timeout=120)
            
            print("✅ [6-QADAM] Muvaffaqiyatli yakunlandi!")
            await bot.delete_message(chat_id=message.chat.id, message_id=status.message_id)
        else:
            await status.edit_text("❌ Xatolik: Video fayl topilmadi.")

    except Exception as e:
        print(f"❌ KRITIK XATO [HANDLER BLOCK]:")
        traceback.print_exc()
        await status.edit_text(f"❌ Xato: {e}")

    finally:
        if os.path.exists(user_folder):
            shutil.rmtree(user_folder, ignore_errors=True)


async def main():
    print("🤖 Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
