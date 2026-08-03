import os
import shutil
import asyncio

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
async def start(message: types.Message):
    await message.answer(
        "👋 Salom!\n\n"
        "YouTube Shorts linkini yuboring.\n"
        "Men videoni original sifatida yuboraman."
    )


@dp.message()
async def download_short(message: types.Message):

    url = message.text.strip()

    if (
        "youtube.com/shorts/" not in url
        and
        "youtu.be/" not in url
    ):
        await message.answer(
            "❌ Faqat YouTube Shorts linkini yuboring."
        )
        return

    status = await message.answer(
        "⏳ Yuklanmoqda..."
    )

    user_folder = os.path.join(
        DOWNLOAD_DIR,
        str(message.from_user.id)
    )

    os.makedirs(
        user_folder,
        exist_ok=True
    )

    try:

        ydl_opts = {
            "outtmpl": os.path.join(
                user_folder,
                "%(title)s.%(ext)s"
            ),
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "quiet": True,
            "noplaylist": True
        }

        with yt_dlp.YoutubeDL(
            ydl_opts
        ) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            filename = ydl.prepare_filename(
                info
            )

        if not os.path.exists(filename):

            for file in os.listdir(user_folder):

                if file.endswith(".mp4"):
                    filename = os.path.join(
                        user_folder,
                        file
                    )
                    break

        if not os.path.exists(filename):

            await status.edit_text(
                "❌ Video topilmadi."
            )
            return

        await message.answer_video(
            video=FSInputFile(filename),
            supports_streaming=True
        )

        await bot.delete_message(
            chat_id=message.chat.id,
            message_id=status.message_id
        )

    except Exception as e:

        print(e)

        await status.edit_text(
            f"❌ Xatolik:\n{e}"
        )

    finally:

        shutil.rmtree(
            user_folder,
            ignore_errors=True
        )


async def main():

    await dp.start_polling(bot)


if __name__ == "__main__":

    asyncio.run(main())
