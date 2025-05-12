# Case Study Scraper Projesi

## Proje Amacı

Bu proje, belirli bir API'den kamp alanı verilerini çekip doğrulayan, veritabanına kaydeden ve tüm hata yönetimini profesyonel şekilde loglayan, Docker ve zamanlayıcı (APScheduler) ile tam uyumlu bir Python scraper uygulamasıdır.

---

## Kapsam ve Özellikler

- API'den kamp alanı verisi çekme ve doğrulama
- Veritabanına kayıt ve güncelleme (PostgreSQL, SQLAlchemy ORM)
- Kapsamlı loglama (JSON formatında, seviyeli: DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Sadece app.log dosyası kullanılır, tüm önemli olaylar ve hatalar burada tutulur
- Zamanlayıcı ile otomatik veri çekme (APScheduler)
- Docker ile kolay kurulum ve çalıştırma
- Hata yönetimi: Ağ, veri ayrıştırma, zaman aşımı, geçersiz veri, doğrulama ve veritabanı hataları için özel loglama

---

## Klasör ve Dosya Yapısı

```
case_study/
├── app.log                # Tüm loglar burada tutulur (JSON formatında)
├── docker-compose.yml     # Docker servis tanımları
├── Dockerfile             # Uygulama imajı
├── main.py                # Ana uygulama ve zamanlayıcı başlatıcı
├── requirements.txt       # Python bağımlılıkları
├── logs/
│   └── app.log            # Log dosyası (loglar buraya da yazılır)
└── src/
    ├── config.py          # Ortam ve uygulama ayarları
    ├── utils/
    │   ├── logger.py      # Loglama ve hata yönetimi
    │   └── utils.py       # Yardımcı fonksiyonlar
    ├── db/
    │   ├── base.py        # SQLAlchemy base ve bağlantı
    │   ├── db.py          # Veritabanı işlemleri (insert, update, init)
    │   └── models.py      # ORM modelleri
    ├── models/
    │   └── campground.py  # Pydantic veri modeli ve doğrulama
    ├── scraper/
    │   ├── scraper.py     # API'den veri çekme ve işleme
    │   ├── scheduler.py   # Zamanlayıcı fonksiyonları
    │   └── updater.py     # (Geliştirilebilir) Güncelleyici fonksiyonlar
    └── api/
        └── endpoints.py   # (Opsiyonel) API endpointleri
```

---

## Kurulum ve Çalıştırma

### Gereksinimler

- Docker ve Docker Compose
- (Geliştirme için) Python 3.8+ ve pip

### Hızlı Başlangıç

#### 1. Docker ile Çalıştırma

```sh
docker compose up --build
```

- Scraper, APScheduler ile **her 2 dakikada bir** otomatik olarak çalışır.
- Loglar `logs/app.log` ve kökteki `app.log` dosyalarına JSON formatında yazılır.

#### 2. Hemen Çalıştırmak için

```sh
docker compose run -e RUN_ON_STARTUP=true scraper
```

veya docker-compose.yml dosyasındaki environment kısmına ekleyin:

```yaml
    environment:
      - RUN_ON_STARTUP=true
```

- Bu şekilde başlatırsanız, scraper docker başlar başlamaz hemen çalışır, ardından zamanlayıcı ile otomatik çalışmaya devam eder.

#### 3. Geliştirici Modunda (Lokal)

```sh
pip install -r requirements.txt
python main.py
```

---

## Loglama Sistemi

- Tüm loglar JSON formatında, `logs/app.log` ve kökteki `app.log` dosyalarına yazılır.
- Log seviyeleri: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Her logda: zaman, seviye, modül, fonksiyon adı, hata türü (errtype), mesaj ve varsa exception detayları bulunur.
- Hata türleri: NETWORK_ERROR, DATA_PARSE_ERROR, TIMEOUT_ERROR, INVALID_DATA_ERROR, VALIDATION, DB, TYPE, HTTP, GENERIC, NO_ERROR
- Hangi fonksiyonda hangi hata oluştuğu logda açıkça görünür.

---

## Ana Fonksiyonlar ve Amaçları

### main.py

- Uygulamanın giriş noktasıdır.
- Zamanlayıcıyı başlatır ve loglamayı başlatır.
- RUN_ON_STARTUP ile başlatılırsa scraper hemen çalışır.

### src/scraper/scraper.py

- `run_scraper_job`: API'den veri çeker, doğrular ve veritabanına kaydeder. Her çalıştırmada bir defa işini yapar.
- API yanıt kodunu ve işlem süresini loglar.

### src/scraper/scheduler.py

- `start_scheduler`: APScheduler ile scraper'ı belirli aralıklarla (örn. 2 dakika) veya cron ile (örn. gece 03:00) çalıştırır.

### src/db/db.py

- `init_db`: Veritabanı bağlantısı ve tablo oluşturma işlemlerini yönetir, retry ile güvenli hale getirir.
- `insert_campground_to_db`: Doğrulanmış kamp alanı verisini veritabanına ekler veya günceller.

### src/models/campground.py

- `Campground`: Pydantic ile API'den gelen verinin doğrulamasını yapar.
- `CampgroundORM`: SQLAlchemy ile veritabanı modelini tanımlar.
- `prepare_data_for_db`: Doğrulanmış veriyi veritabanına uygun formata çevirir.

### src/utils/logger.py

- Kapsamlı loglama ve hata yönetimi sağlar.
- `handle_exception`: Tüm hata türlerini seviyeli ve fonksiyon adıyla birlikte loglar.
- Özel hata türleri: NetworkError, DataParseError, TimeoutError, InvalidDataError, DatabaseException, ValidationException

### src/utils/utils.py

- `retry_operation`: Tüm kritik işlemler için otomatik retry ve exponential backoff sağlar.
- `sanitize_data`: Verileri özel karakterlerden arındırır.

---

## Hata Yönetimi ve Loglama

- Tüm hatalar (ağ, veri ayrıştırma, zaman aşımı, geçersiz veri, doğrulama, veritabanı, HTTP, tip, bilinmeyen) `handle_exception` fonksiyonu ile merkezi olarak yönetilir.
- Loglarda fonksiyon adı ve hata türü açıkça görünür.
- Hata olmayan loglarda errtype: NO_ERROR olarak yazılır.

---

## Sık Kullanılan Komutlar

**Standart başlatma:**

```sh
docker compose up --build
```

**Hemen çalıştırmak için:**

```sh
docker compose run -e RUN_ON_STARTUP=true scraper
```

**Logları görmek için:**

```sh
tail -f logs/app.log
```

---

## Sıkça Sorulanlar

- **Konteyner kapalıysa cron çalışır mı?**
  - Hayır, konteyner açık olmalı. Zamanlayıcı arka planda bekler.
- **Zamanlamayı nasıl değiştiririm?**
  - `src/scraper/scheduler.py` içinde APScheduler satırında aralığı veya cron ifadesini değiştir.
- **Veritabanı bağlantısı veya HTTP hatalarında ne olur?**
  - Otomatik retry ve loglama ile hata yönetimi yapılır, tüm detaylar app.log'da tutulur.

---

## Katkı ve Geliştirme

- Kodun tamamı PEP8 uyumlu ve sürdürülebilir şekilde yazılmıştır.
- Yeni fonksiyonlar eklerken merkezi hata yönetimi ve loglama yapısını kullanmaya devam edin.
- Zamanlama ve ENV değişkenleri ile davranış kontrolünü koruyun.

---

## İletişim

Her türlü soru ve katkı için proje sahibiyle iletişime geçebilirsiniz.
