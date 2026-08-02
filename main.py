import os
import glob
import time
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import yt_dlp
import instaloader

TOKEN = "8915219066:AAEapW0Id_nw6Ex1hZsm8tcTxmR4x8k-Zag"

bot = Bot(token=TOKEN)
dp = Dispatcher()

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
    await message.answer("Salom! Menga Instagram yoki YouTube havolasini yuboring.")

@dp.message()
async def process_link_handler(message: types.Message):
    url = message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await message.answer("❌ Iltimos, to'g'ri havola yuboring!")
        return

    processing_msg = await message.answer("⏳ Yuklab olinmoqda, biroz kuting...")
    
    download_dir = f"downloads_{message.from_user.id}"
    os.makedirs(download_dir, exist_ok=True)

    error_log = ""

    try:
        # 1. Agar havola Instagram Post (karusel/rasm) bo'lsa
        if "/p/" in url:
            try:
                shortcode = url.split("/p/")[1].split("/")[0]
                post = instaloader.Post.from_shortcode(L.context, shortcode)
                L.download_post(post, target=download_dir)
            except Exception as e:
                error_log += f"\n- Instaloader Post xatosi: {str(e)}"

        # 2. Agar havola Instagram Profil (story uchun) bo'lsa
        elif "instagram.com/" in url and not ("/reel/" in url) and not ("/tv/" in url):
            parts = [p for p in url.split("/") if p]
            if len(parts) >= 3:
                username = parts[-1]
                if username in ["instagram.com", "www.instagram.com"]:
                    username = parts[-2]
                try:
                    profile = instaloader.Profile.from_username(L.context, username)
                    for story in L.get_stories([profile.userid]):
                        for item in story.get_items():
                            L.download_storyitem(item, target=download_dir)
                except Exception as e:
                    error_log += f"\n- Profil/Story xatosi (429 Blok yoki Yopiq profil): {str(e)}"

        # 3. Qolgan hamma narsa (Reels, YouTube va boshqalar) uchun yt-dlp
        else:
            ydl_opts = {
                'outtmpl': f'{download_dir}/%(id)s.%(ext)s',
                'format': 'best/bestvideo+bestaudio/best',
                'cookiefile': 'cookies.txt',
                'ignoreerrors': True,
                'quiet': True,
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(url, download=True)
            except Exception as e:
                error_log += f"\n- Yt-dlp xatosi: {str(e)}"

        # Papkadagi barcha yuklangan fayllarni yig'ish va dublyorlarni olib tashlash
        extensions = ('*.jpg', '*.jpeg', '*.png', '*.webp', '*.mp4', '*.mov', '*.mkv', '*.webm')
        found_files = []
        for ext in extensions:
            found_files.ext(glob.glob(os.path.join(download_dir, '**', ext), recursive=True)) if hasattr(found_files, 'ext') else found_files.extend(glob.glob(os.path.join(download_dir, '**', ext), recursive=True))

        downloaded_files = sorted(list(set([os.path.abspath(f) for f in found_files if os.path.exists(f)])))

        if downloaded_files:
            await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
            for file_path in downloaded_files:
                try:
                    if file_path.endswith(('.jpg', '.jpeg', '.png', '*.webp')):
                        await message.answer_photo(photo=types.FSInputFile(file_path))
                    elif file_path.endswith(('.mp4', '.mov', '*.mkv', '*.webm')):
                        await message.answer_video(video=types.FSInputFile(file_path))
                    time.sleep(0.5)except Exception as file_err:
                    print(f"Yuborish xatosi: {file_err}")
        else:
            # Aniq qayerda xatolik ketganini ekranga chiqarish
            err_details = error_log if error_log else "Media fayllari topilmadi yoki havola yaroqsiz."
            await bot.edit_message_text(
                f"❌ **Yuklab bo'lmadi!**\n"
                f"🔍 Aniqlangan sabab: `{err_details}`", 
                chat_id=message.chat.id, 
                message_id=processing_msg.message_id,
                parse_mode="Markdown"
            )

    except Exception as e:
        print(f"ASOSIY XATOLIK: {str(e)}")
        await bot.edit_message_text(
            f"❌ **Xatolik yuz berdi!**\n\n"
            f"🛠 Sabab: `{str(e)}`", 
            chat_id=message.chat.id, 
            message_id=processing_msg.message_id,
            parse_mode="Markdown"
        )

    finally:
        for file_path in glob.glob(os.path.join(download_dir, '**', '*.*'), recursive=True):
            try:
                os.remove(file_path)
            except:
                pass
        try:
            os.rmdir(download_dir)
        except:
            pass

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
