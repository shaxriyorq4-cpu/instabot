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

# Instaloader ni sozlash (istoriyalar va rasmlar uchun)
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
    await message.answer("Salom! Menga Instagram (profil, post, rasmlar, reel, story) yoki YouTube havolasini yuboring, men uni yuklab beraman.")

@dp.message()
async def process_link_handler(message: types.Message):
    url = message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        await message.answer("❌ Iltimos, to'g'ri havola yuboring!")
        return

    processing_msg = await message.answer("⏳ Yuklab olinmoqda, biroz kuting...")
    
    downloaded_files = []
    download_dir = f"downloads_{message.from_user.id}"
    os.makedirs(download_dir, exist_ok=True)

    try:
        # 1. Instagram profil havolasi bo'lsa (istoriyalarini olish uchun)
        if "instagram.com/" in url and ("/p/" not in url) and ("/reel/" not in url):
            parts = [p for p in url.split("/") if p]
            if len(parts) >= 3:
                username = parts[-1]
                if username == "instagram.com" or username == "www.instagram.com":
                    username = parts[-2]
                
                try:
                    profile = instaloader.Profile.from_username(L.context, username)
                    for story in L.get_stories([profile.userid]):
                        for item in story.get_items():
                            L.download_storyitem(item, target=download_dir)
                except Exception as story_err:
                    print(f"Istorya yuklashda xatolik: {story_err}")

        # 2. Instagram post / karusel bo'lsa
        if "instagram.com/p/" in url:
            try:
                shortcode = url.split("/p/")[1].split("/")[0]
                post = instaloader.Post.from_shortcode(L.context, shortcode)
                L.download_post(post, target=download_dir)
            except Exception as inst_err:
                print(f"Instaloader post xatosi: {inst_err}")

        # 3. Reels, YouTube va boshqa videolar uchun yt-dlp
        ydl_opts = {
            'outtmpl': f'{download_dir}/%(id)s_%(autonumber)s.%(ext)s',
            'format': 'best/bestvideo+bestaudio/best',
            'cookiefile': 'cookies.txt',
            'ignoreerrors': True,
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info and 'entries' in info:
                for entry in info['entries']:
                    if entry:
                        filename = ydl.prepare_filename(entry)
                        downloaded_files.append(filename)
            elif info:
                filename = ydl.prepare_filename(info)
                downloaded_files.append(filename)

        # Papkadagi barcha fayllarni to'liq yig'ish (ichki papkalardan ham)
        extensions = ('*.jpg', '*.jpeg', '*.png', '*.webp', '*.mp4', '*.mov', '*.mkv', '*.webm')
        for ext in extensions:
            downloaded_files.extend(glob.glob(os.path.join(download_dir, '**', ext), recursive=True))

        # Unikal fayllarni to'plash
        downloaded_files = sorted(list(set([os.path.abspath(f) for f in downloaded_files if os.path.exists(f)])))

        if downloaded_files:
            for file_path in downloaded_files:
                try:
                    if file_path.endswith(('.jpg', '.jpeg', '.png', '*.webp')):
                        media_file = types.FSInputFile(file_path)
                        await message.answer_photo(photo=media_file)
                    elif file_path.endswith(('.mp4', '*.mov', '*.mkv', '*.webm')):
                        media_file = types.FSInputFile(file_path)
                        await message.answer_video(video=media_file)
                    time.sleep(1)
                except Exception as file_err:
                    print(f"Faylni yuborishda xatolik: {file_err}")
            
            await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
        else:
            await bot.edit_message_text(
                "❌ Media topilmadi. Profil yopiq bo'lishi mumkin yoki hozirda aktiv istoriyasi yo'q.", 
                chat_id=message.chat.id, 
                message_id=processing_msg.message_id
            )

    except Exception as e:
        error_text = str(e)
        print(f"ANIQ XATOLIK: {error_text}")
        
        await bot.edit_message_text(
            f"❌ **Xatolik yuz berdi!**\n\n"
            f"🛠 Sabab: `{error_text}`", 
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
