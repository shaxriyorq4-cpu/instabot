import os
import glob
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import yt_dlp
import instaloader
import shutil

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
    
    if not url.startswith(("http://", "https://")):
        await message.answer("❌ Iltimos, to'g'ri havola yuboring!")
        return

    processing_msg = await message.answer("⏳ Yuklab olinmoqda, biroz kuting...")
    
    download_dir = f"downloads_{message.from_user.id}"
    os.makedirs(download_dir, exist_ok=True)

    error_log = ""

    try:
        success_insta = False
        try:
            if "/p/" in url or "/reel/" in url or "/tv/" in url:
                if "/p/" in url:
                    shortcode = url.split("/p/")[1].split("/")[0]
                elif "/reel/" in url:
                    shortcode = url.split("/reel/")[1].split("/")[0]
                else:
                    shortcode = url.split("/tv/")[1].split("/")[0]
                    
                post = instaloader.Post.from_shortcode(L.context, shortcode)
                L.download_post(post, target=download_dir)
                success_insta = True

            elif "instagram.com/" in url and not any(x in url for x in ["/p/", "/reel/", "/tv/"]):
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
                        success_insta = True
                    except Exception as limit_err:
                        error_log += f"\n- Story limiti (429): Instagram vaqtincha blokladi."
        except Exception as e:
            error_log += f"\n- Instaloader xatosi: {str(e)}"

        if not success_insta or not glob.glob(os.path.join(download_dir, '**', '*.*'), recursive=True):
            ydl_opts = {
                'outtmpl': f'{download_dir}/%(id)s.%(ext)s',
                'format': 'best/bestvideo+bestaudio/best',
                'ignoreerrors': True,
                'quiet': True,
            }

            if os.path.exists("cookies.txt"):
                ydl_opts["cookiefile"] = "cookies.txt"
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(url, download=True)
            except Exception as e:
                error_log += f"\n- Yt-dlp xatosi: {str(e)}"

        extensions = ('*.jpg', '*.jpeg', '*.png', '*.webp', '*.heic', '*.mp4', '*.mov', '*.mkv', '*.webm')
        found_files = []
        for ext in extensions:
            found_files.extend(glob.glob(os.path.join(download_dir, '**', ext), recursive=True))

        downloaded_files = sorted(list(set([os.path.abspath(f) for f in found_files if os.path.exists(f)])))

        if downloaded_files:
            await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
            
            photo_media = []
            video_media = []

            for file_path in downloaded_files:
                if file_path.endswith(('.jpg', '.jpeg', '.png', '.webp', '.heic')) and os.path.getsize(file_path) > 1024:
                    photo_media.append(file_path)
                elif file_path.endswith(('.mp4', '.mov', '.mkv', '.webm')):
                    video_media.append(file_path)

            if photo_media:
                chunked_photos = [photo_media[i:i + 10] for i in range(0, len(photo_media), 10)]
                for chunk in chunked_photos:
                    media_group = [types.InputMediaPhoto(media=types.FSInputFile(p)) for p in chunk]
                    try:
                        await bot.send_media_group(chat_id=message.chat.id, media=media_group)
                    except Exception as e:
                        print(f"Rasm yuborish xatosi: {e}")

            for v_path in video_media:
                try:
                    await message.answer_video(video=types.FSInputFile(v_path))
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"Video yuborish xatosi: {e}")

        else:
            err_details = error_log if error_log.strip() else "Media fayllari topilmadi yoki havola yaroqsiz."
            await bot.edit_message_text(
                f"❌ **Yuklab bo'lmadi!**\n\n"
                f"🔍 **Sabab:**\n`{err_details}`", 
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
                if os.path.isfile(file_path):
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
