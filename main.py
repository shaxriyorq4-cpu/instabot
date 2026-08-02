import os
import glob
import time
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import yt_dlp

TOKEN = "8915219066:AAEapW0Id_nw6Ex1hZsm8tcTxmR4x8k-Zag"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Salom! Menga Instagram (post, rasmlar, reel, story) yoki YouTube havolasini yuboring, men uni yuklab beraman.")

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
        ydl_opts = {
            'outtmpl': f'{download_dir}/%(id)s_%(autonumber)s.%(ext)s',
            'format': 'best/bestvideo+bestaudio/best',
            'cookiefile': 'cookies.txt',
            'ignoreerrors': True,  # Video topilmasa ham rasmlarni yuklab berishda davom etishi uchun
            'writethumbnail': False,
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

        # Papkadagi barcha rasm va videolarni to'liq terib olish
        extensions = ('*.jpg', '*.jpeg', '*.png', '*.webp', '*.mp4', '*.mov', '*.mkv', '*.webm')
        for ext in extensions:
            downloaded_files.extend(glob.glob(os.path.join(download_dir, ext)))

        # Unikal fayllarni saralash
        downloaded_files = sorted(list(set([os.path.abspath(f) for f in downloaded_files if os.path.exists(f)])))

        if downloaded_files:
            for file_path in downloaded_files:
                try:
                    if file_path.endswith(('.jpg', '*.jpeg', '*.png', '*.webp')):
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
                "❌ Media topilmadi yoki bu post faqat rasmdan iborat bo'lib, uni o'qishda cheklov bor.", 
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
