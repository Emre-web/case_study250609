# Python 3.11 slim tabanlı bir Docker imajı kullanılıyor
FROM python:3.11-slim

# Python'un bytecode dosyalarını yazmasını engelle ve tamponlamayı devre dışı bırak
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Çalışma dizinini /app olarak ayarla
WORKDIR /app

# Sistem bağımlılıklarını yükle
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Pip'i güncelle ve Python bağımlılıklarını yükle
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install watchdog  # Dosya izleme için watchdog yükleniyor

# Uygulama kodlarını kopyala
COPY . .

# Python önbellek dosyalarını temizle
RUN find . -name '*.pyc' -delete

# Uygulamayı başlat ve dosya değişikliklerini izlemek için watchmedo kullan
CMD ["sh", "-c", "find . -name '*.pyc' -delete && watchmedo auto-restart --directory=/app --patterns=*.py --recursive -- python main.py"]
