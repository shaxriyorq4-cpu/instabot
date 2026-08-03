FROM python:3.11-slim

# Kerakli dasturlar va Deno ni o'rnatish
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Deno ni o'rnatish (yt-dlp ning n-challenge ni yechishi uchun shart)
RUN curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh

WORKDIR /app

# Talab qilingan kutubxonalarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
