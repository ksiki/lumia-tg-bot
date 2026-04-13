FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libreoffice-writer \
    libreoffice-calc \
    fonts-noto-color-emoji \
    fontconfig \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

RUN fc-cache -f -v

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /tmp/libreoffice_profile && chmod 777 /tmp/libreoffice_profile

CMD ["python", "bot/aiogram_run.py"]