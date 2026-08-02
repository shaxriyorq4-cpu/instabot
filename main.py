import os
import glob
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import yt_dlp
import shutil

TOKEN = "8915219066:AAEapW0Id_nw6Ex1hZsm8tcTxmR4x8k-Zag"

bot = Bot(token=TOKEN)
dp = Dispatcher()

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
        ydl_opts = {
            'outtmpl': f'{download_dir}/%(id)s_%(autonumber)s.%(ext)s',
            'format': 'best/bestvideo+bestaudio/best',
            'ignoreerrors': True,
            'quiet': True,
            'noplaylist': False,
        }

        if os.path.exists("cookies.txt"):
            ydl_opts["cookiefile"] = "cookies.txt"
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
        except Exception as e:
            error_log = str(e)

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
            err_details = error_log if error_log else "Fayl topilmadi yoki havola yaroqsiz."
            await bot.edit_message_text(
                f"❌ **Yuklab bo'lmadi!**\n\n"
                f"🔍 **Aniq xato:**\n`{err_details}`", 
                chat_id=message.chat.id,
                message_id=processing_msg.message_id,
                parse_mode="Markdown"
            )

    except Exception as e:
        print(f"ASOSIY XATOLIK: {str(e)}")
        await bot.edit_message_text(
            f"❌ **Xatolik yuz berdi!**\n\n"
            f"🛠 Tafsilot: `{str(e)}`", 
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
        try:os.rmdir(download_dir)
        except:
            pass

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
