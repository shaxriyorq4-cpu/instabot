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
    await message.answer("Salom! Link yuboring, raqamlarni sanab, videoni chaqmoq tezligida tashlab beraman. ⚡️")


@dp.message()
async def link_handler(message: types.Message):
    url = message.text.strip()
    
    if not url.startswith(("http://", "https://")):
        await message.answer("❌ To'g'ri link yuboring.")
        return

    # 1-2-3 gacha sanash animatsiyasini boshlaymiz
    status = await message.answer("⚡ 1...")
    await asyncio.sleep(0.4)
    
    try:
        await status.edit_text("⚡ 2...")
    except:
        pass
    
    await asyncio.sleep(0.4)
    
    try:
        await status.edit_text("⚡ 3...")
    except:
        pass

    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
        }
        
        # 1-USUL: ULTRATEZKOR (Link orqali to'g'ridan-to'g'ri tashlash)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            direct_url = info.get('url')
        
        if direct_url:
            try:
                await message.answer_video(video=direct_url)
                await bot.delete_message(chat_id=message.chat.id, message_id=status.message_id)
                print("✅ 1 SEKUNDLIK USUL ISHLADI!")
                return
            except Exception as direct_err:
                print(f"⚠️ 1-usul o'xshamadi, 2-usulga o'tamiz: {direct_err}")
        
        # 2-USUL: STANDART TEZKOR (Yuklab yuborish)
        user_folder = os.path.join(DOWNLOAD_DIR, str(message.from_user.id))
        os.makedirs(user_folder, exist_ok=True)
        
        ydl_opts['outtmpl'] = os.path.join(user_folder, '%(id)s.%(ext)s')
        ydl_opts['concurrent_fragment_downloads'] = 5
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        if os.path.exists(filename):
            video_file = FSInputFile(filename)
            await message.answer_video(video=video_file, request_timeout=120)
            await bot.delete_message(chat_id=message.chat.id, message_id=status.message_id)
            print("✅ 2-USUL (Yuklab yuborish) orqali ishlandi!")
            shutil.rmtree(user_folder, ignore_errors=True)
        else:
            await status.edit_text("❌ Video topilmadi.")

    except Exception as e:
        print("❌ XATOLIK:")
        traceback.print_exc()
        await status.edit_text("❌ Video yuklashda xatolik yuz berdi.")


async def main():
    print("🚀 Ultratezkor bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
