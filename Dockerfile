FROM python:3.10-slim

# Kerakli tizim paketlari va ffmpeg'ni o'rnatish
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Ishchi katalogni belgilash
WORKDIR /app

# Kutubxonalarni o'rnatish uchun fayllarni ko'chirish
COPY requirements.txt .

# Python kutubxonalarini o'rnatish
RUN pip install --no-cache-dir -r requirements.txt

# Qolgan barcha fayllarni ko'chirish
COPY . .

# Botni ishga tushirish
CMD ["python", "main.py"]
