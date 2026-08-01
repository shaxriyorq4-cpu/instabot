import os
import glob
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import instaloader
import yt_dlp

# Bot tokeningizni qo'shtirnoq ichiga yozing (masalan: "123456789:ABCdefGhIJK...")
TOKEN = "TOKENINGIZNI_SHU_YERGA_YOZING"

bot = Bot(token=8915219066:AAEapW0Id_nw6Ex1hZsm8tcTxmR4x8k-Zag)
dp = Dispatcher()

# Instaloader sozlamasi
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
    await message.answer("Salom! Menga Instagram yoki YouTube havolasini yuboring, men uni yuklab beraman.")

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
        if "instagram.com" in url:
            shortcode = None
            if "/p/" in url:
                shortcode = url.split("/p/")[1].split("/")[0]
            elif "/reel/" in url:
                shortcode = url.split("/reel/")[1].split("/")[0]
            elif "/reels/" in url:
                shortcode = url.split("/reels/")[1].split("/")[0]

            if shortcode:
                post = instaloader.Post.from_shortcode(L.context, shortcode)
                L.download_post(post, target=download_dir)
                
                extensions = ('*.jpg', '*.jpeg', '*.png', '*.webp', '*.mp4', '*.mov', '*.mkv', '*.webm')
                for ext in extensions:
                    downloaded_files.extend(glob.glob(os.path.join(download_dir, ext)))
            else:
                await message.answer("❌ Instagram havolasidan postni aniqlab bo'lmadi.")
                await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
                return
        else:
            ydl_opts = {
                'outtmpl': f'{download_dir}/%(id)s.%(ext)s',
                'format': 'best',
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                downloaded_files.append(filename)

        if downloaded_files:
            downloaded_files.sort()
            
            for file_path in downloaded_files:
                try:
                    if file_path.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        media_file = types.FSInputFile(file_path)
                        await message.answer_photo(photo=media_file)
                    elif file_path.endswith(('.mp4', '.mov', '.mkv', '.webm')):
                        media_file = types.FSInputFile(file_path)
                        await message.answer_video(video=media_file)
                except Exception as file_err:
                    print(f"Faylni yuborishda xatolik: {file_err}")
            
            await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
        else:
            await bot.edit_message_text("❌ Hech qanday media topilmadi yoki yuklab bo'lmadi.", chat_id=message.chat.id, message_id=processing_msg.message_id)

    except Exception as e:
        await bot.edit_message_text(f"❌ Xatolik yuz berdi: {e}", chat_id=message.chat.id, message_id=processing_msg.message_id)

    finally:
        for file_path in glob.glob(os.path.join(download_dir, '*.*')):
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
