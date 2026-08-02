import os
import glob
import shutil
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

import yt_dlp
import instaloader


TOKEN = "8915219066:AAEapW0Id_nw6Ex1hZsm8tcTxmR4x8k-Zag"

bot = Bot(token=TOKEN)
dp = Dispatcher()


DOWNLOAD_ROOT = "downloads"

os.makedirs(
    DOWNLOAD_ROOT,
    exist_ok=True
)


L = instaloader.Instaloader(
    download_videos=False,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False
)



@dp.message(Command("start"))
async def start_handler(
    message: types.Message
):

    await message.answer(
        "Salom! 👋\n\n"
        "Instagram yoki YouTube havolasini yuboring.\n"
        "Media faylni yuklab beraman."
    )



def get_files(folder):

    files = []

    extensions = (
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.webp",
        "*.mp4",
        "*.mov",
        "*.mkv",
        "*.webm"
    )


    for ext in extensions:

        files.extend(
            glob.glob(
                os.path.join(
                    folder,
                    ext
                )
            )
        )


    return [
        os.path.abspath(file)
        for file in files
        if os.path.exists(file)
    ]



async def download_instagram_post(
    url,
    folder
):

    try:

        shortcode = (
            url
            .split("/p/")[1]
            .split("/")[0]
        )


        post = instaloader.Post.from_shortcode(
            L.context,
            shortcode
        )


        L.download_post(
            post,
            target=folder
        )


    except Exception as e:

        print(
            "Instagram post xatosi:",
            e
        )



async def download_media(
    url,
    folder
):

    files = []


    if "instagram.com/p/" in url:

        await download_instagram_post(
            url,
            folder
        )



    ydl_options = {

        "outtmpl":
        f"{folder}/%(id)s_%(autonumber)s.%(ext)s",

        "format":
        "best/bestvideo+bestaudio/best",

        "cookiefile":
        "cookies.txt",

        "ignoreerrors":
        True,

        "quiet":
        True
    }



    try:

        with yt_dlp.YoutubeDL(
            ydl_options
        ) as ydl:

            ydl.extract_info(
                url,
                download=True
            )


    except Exception as e:

        print(
            "Yuklash xatosi:",
            e
        )



    files = get_files(
        folder
    )


    return files



async def send_files(
    message,
    files
):


    for file in files:

        try:

            ext = file.lower()


            if ext.endswith(
                (
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".webp"
                )
            ):

                await message.answer_photo(
                    photo=types.FSInputFile(
                        file
                    )
                )


            elif ext.endswith(
                (
                    ".mp4",
                    ".mov",
                    ".mkv",
                    ".webm"
                )
            ):

                size = os.path.getsize(
                    file
                )


                if size <= 50 * 1024 * 1024:

                    await message.answer_video(
                        video=types.FSInputFile(
                            file
                        )
                    )

                else:

                    await message.answer(
                        "❌ Video 50 MB dan katta."
                    )


            await asyncio.sleep(
                1
            )


        except Exception as e:

            print(
                "Yuborish xatosi:",
                e
            )



@dp.message()
async def process_link_handler(
    message: types.Message
):

    url = message.text.strip()


    if not url.startswith(
        (
            "http://",
            "https://"
        )
    ):

        await message.answer(
            "❌ To'g'ri havola yuboring."
        )

        return



    status = await message.answer(
        "⏳ Yuklanmoqda..."
    )



    user_folder = os.path.join(
        DOWNLOAD_ROOT,
        str(message.from_user.id)
    )


    os.makedirs(
        user_folder,
        exist_ok=True
    )



    try:


        files = await download_media(
            url,
            user_folder
        )


        if files:

            await send_files(
                message,
                files
            )


            await bot.delete_message(
                chat_id=message.chat.id,
                message_id=status.message_id
            )


        else:

            await status.edit_text(
                "❌ Media topilmadi."
            )



    except Exception as e:

        print(
            "Asosiy xato:",
            e
        )


        await status.edit_text(
            f"❌ Xatolik:\n{e}"
        )



    finally:


        if os.path.exists(
            user_folder
        ):

            shutil.rmtree(
                user_folder,
                ignore_errors=True
            )



async def main():

    await dp.start_polling(
        bot
    )



if __name__ == "__main__":

    asyncio.run(
        main()
    )
