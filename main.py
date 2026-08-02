import os
from instagrapi import Client

def instagram_bot_yuklash():
    # Instagramga kirish ma'lumotlari
    USERNAME = "instadown_v2_bot"
    PASSWORD = "Instadownv2"

    cl = Client()
    
    try:
        print("Instagramga ulanmoqda...")
        cl.login(USERNAME, PASSWORD)
        print("Muvaffaqiyatli kirdingiz!")
    except Exception as e:
        print(f"Kirishda xatolik yuz berdi: {e}")
        return

    # 1. Istoriyaga qo'yiladigan rasmlar ro'yxati 
    stories_photos = [
        "story1.jpg", 
        "story2.jpg", 
        "story3.jpg"
    ]

    # 2. Videolar ro'yxati
    videos = [
        "video1.mp4", 
        "video2.mp4"
    ]

    # XATOLIKNI OLDINI OLISH: Ro'yxatdagi dublikatlarni (takroriy fayllarni) tozalaymiz
    stories_photos = list(dict.fromkeys(stories_photos))
    videos = list(dict.fromkeys(videos))

    print("\n--- Istoriyalarni yuklash boshlandi ---")
    for photo in stories_photos:
        if os.path.exists(photo):
            try:
                cl.photo_to_story(photo)
                print(f"[+] Istoriya yuklandi: {photo}")
            except Exception as e:
                print(f"[-] Xatolik rasm yuklashda ({photo}): {e}")
        else:
            print(f"[XATO] Bunday rasm topilmadi yoki yo'li noto'g'ri: {photo}")

    print("\n--- Videolarni yuklash boshlandi ---")
    for video in videos:
        if os.path.exists(video):
            try:
                cl.video_upload_to_story(video)
                print(f"[+] Video istoriyaga yuklandi: {video}")
            except Exception as e:
                print(f"[-] Xatolik video yuklashda ({video}): {e}")
        else:
            print(f"[XATO] Bunday video topilmadi yoki yo'li noto'g'ri: {video}")

    print("\nBarcha amallar bajarib bo'lindi!")

if __name__ == "__main__":
    instagram_bot_yuklash()
