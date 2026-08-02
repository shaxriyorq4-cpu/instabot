import os
import asyncio
import traceback

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import yt_dlp


TOKEN = "8915219066:AAGSCkzvFImev5HLBdOMqv-q8CWjraGnsHg"

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Salom! Link yuboring, chaqmoq tezligida tashlab beraman. ⚡️")


async def get_direct_url(url: str):
    """Instagram'dan videoning yashirin direct havolasini sekundida sug'urib olish"""
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
        }
        # download=False orqali faylni serverga skachat qilmaymiz, faqat havolani olamiz
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('url')
    except Exception as e:
        print(f"Havolani olishda xato: {e}")
    return None


@dp.message()
async def link_handler(message: types.Message):
    url = message.text.strip()
    
    if not url.startswith(("http://", "https://")):
        await message.answer("❌ To'g'ri link yuboring.")
        return

    # 1. Havolani orqa fonda darhol qidirishni boshlaymiz
    link_task = asyncio.create_task(get_direct_url(url))

    # 2. Sanoqni boshlaymiz
    status = await message.answer("⚡ 1...")
    
    steps = ["⚡ 2...", "⚡ 3..."]
    for step_text in steps:
        # Havola topilganini har 0.2 sekundda tekshirib boramiz
        for _ in range(2):
            if link_task.done():
                break
            await asyncio.sleep(0.1)
            
        if link_task.done():
            break
            
        try:
            await status.edit_text(step_text)
        except:
            pass

    # Havolaning tayyor bo'lishini kutamiz (odatda bu juda tez ishlaydi)
    direct_url = await link_task

    try:
        if direct_url:
            # Telegramning o'zi videoni to'g'ridan-to'g'ri tortib oladi (fayl yuklab o'tirilmaydi)
            await message.answer_video(video=direct_url)
            
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=status.message_id)
            except:
                pass
            print("✅ Chaqmoq tezligida tashlandi!")
        else:
            await status.edit_text("❌ Videoni topib bo'lmadiki, linkni tekshiring.")
    except Exception as e:
        print(f"Yuborishda xato: {e}")
        try:
            await status.edit_text("❌ Yuborishda xatolik yuz berdi.")
        except:
            pass


async def main():
    print("🚀 Ultratezkor bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
