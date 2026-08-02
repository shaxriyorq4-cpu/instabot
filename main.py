import os
import shutil
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo

import yt_dlp
import instaloader


TOKEN = "8915219066:AAHv2SbrPqW_Tx2eU-zNcLEvYEO5wpgSRWU"

bot = Bot(token=TOKEN)
dp = Dispatcher()


DOWNLOAD_DIR = "downloads"

os.makedirs(
    DOWNLOAD_DIR,
    exist_ok=True
)


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
    await message.answer(
        "Salom! 👋\n\n"
        "Instagram yoki YouTube link yuboring.\n"
        "Media fayllarni yuklab beraman."
    )


def detect_instagram_type(url: str):
    url = url.lower()

    if "/reel/" in url:
        return "reel"

    if "/p/" in url:
        return "post"

    if "/stories/" in url:
        return "story"

    return "unknown"


def get_story_username(url: str):
    try:
        parts = url.rstrip("/").split("/")

        if "stories" in parts:
            index = parts.index("stories")
            return parts[index + 1]

    except Exception as e:
        print("Story username xatosi:", e)

    return None


async def collect_media(folder: str):
    files = []

    for root, dirs, filenames in os.walk(folder):
        for name in filenames:

            if name.lower().endswith(
                (
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".webp",
                    ".mp4",
                    ".mov",
                    ".webm"
                )
            ):
                files.append(
                    os.path.join(
                        root,
                        name
                    )
                )

    files.sort()

    return [
        os.path.abspath(file)
        for file in files
        if os.path.exists(file)
    ]


async def cleanup(folder: str):

    if os.path.exists(folder):

        shutil.rmtree(
            folder,
            ignore_errors=True
        )


async def download_story(
    username: str,
    folder: str
):

    files = []

    try:

        profile = instaloader.Profile.from_username(
            L.context,
            username
        )

        for story in L.get_stories(
            userids=[
                profile.userid
            ]
        ):

            for item in story.get_items():

                L.download_storyitem(
                    item,
                    target=folder
                )

        files = await collect_media(folder)

    except Exception as e:

        print(
            "Story xatosi:",
            e
        )

    return files


async def download_instagram(
    url: str,
    folder: str
):

    media_type = detect_instagram_type(url)

    if media_type == "story":

        username = get_story_username(url)

        if username:

            return await download_story(
                username,
                folder
            )

        return []

    if media_type in (
        "post",
        "reel"
    ):

        try:

            if "/p/" in url:

                shortcode = (
                    url
                    .split("/p/")[1]
                    .split("/")[0]
                )

            else:

                shortcode = (
                    url
                    .split("/reel/")[1]
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

            return await collect_media(folder)

        except Exception as e:

            print(
                "Instagram xatosi:",
                e
            )

            return []

    return []


async def download_youtube(
    url: str,
    folder: str
):

    options = {
        "outtmpl": f"{folder}/%(id)s.%(ext)s",
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "noplaylist": False,
        "ignoreerrors": True,
        "retries": 3,
        "fragment_retries": 3,
        "concurrent_fragment_downloads": 5
    }

    try:

        with yt_dlp.YoutubeDL(
            options
        ) as ydl:

            ydl.extract_info(
                url,
                download=True
            )

    except Exception as e:

        print(
            "YouTube xatosi:",
            e
        )

        return []

    return await collect_media(
        folder
    )


async def send_media_group(
    message: types.Message,
    files: list
):

    media = []

    for file in files:

        ext = file.lower()

        if ext.endswith(
            (
                ".jpg",
                ".jpeg",
                ".png",
                ".webp"
            )
        ):

            media.append(
                InputMediaPhoto(
                    media=FSInputFile(
                        file
                    )
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

                media.append(
                    InputMediaVideo(
                        media=FSInputFile(
                            file
                        )
                    )
                )

            else:

                await message.answer(
                    "❌ Video 50 MB dan katta."
                )

    if not media:

        await message.answer(
            "❌ Media topilmadi."
        )

        return

    try:

        for i in range(
            0,
            len(media),
            10
        ):

            await message.answer_media_group(
                media=media[i:i+10]
            )

            await asyncio.sleep(
                0.5
            )

    except Exception as e:

        print(
            "Yuborish xatosi:",
            e
        )


@dp.message()
async def link_handler(
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
            "❌ Link yuboring."
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

    files = []

    try:

        if "instagram.com" in url:

            files = await download_instagram(
                url,
                user_folder
            )

        elif (
            "youtube.com" in url
            or
            "youtu.be" in url
        ):

            files = await download_youtube(
                url,
                user_folder
            )

        if files:

            await send_media_group(
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

        await cleanup(
            user_folder
        )


async def main():
    await dp.start_polling(
        bot
    )


if __name__ == "__main__":
    asyncio.run(
        main()
    )
