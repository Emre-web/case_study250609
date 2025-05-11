# Case Study Scraper Projesi

## Proje Amacı
Bu proje, belirli bir API'den kamp alanı verilerini çekip doğrulayan, veritabanına kaydeden ve tüm hata yönetimini profesyonel şekilde loglayan, Docker ve zamanlayıcı (APScheduler) ile tam uyumlu bir Python scraper uygulamasıdır.

---

## Hızlı Başlangıç

### 1. Gereksinimler
- Docker ve Docker Compose
- (Geliştirme için) Python 3.8+ ve pip

### 2. Projeyi Çalıştırmak

#### Standart Kullanım (Sadece zamanlanmış çalışır)
```sh
docker compose up --build
```
- Scraper, APScheduler ile **her 2 dakikada bir** otomatik olarak çalışır.
- Zamanlama aralığını kodda kolayca değiştirebilirsiniz (örn. gece 03:00 için `scheduler.add_job(..., 'cron', hour=3, minute=0)`).

#### Hemen Çalıştırmak için (isteğe bağlı)
```sh
docker compose run -e RUN_ON_STARTUP=true scraper
```
veya docker-compose.yml dosyasındaki environment kısmına ekleyin:
```yaml
    environment:
      - RUN_ON_STARTUP=true
```
- Bu şekilde başlatırsanız, scraper docker başlar başlamaz hemen çalışır, ardından zamanlayıcı ile otomatik çalışmaya devam eder.

---

## Proje Yapısı

```
case_study/
├── app.log                # Tüm loglar burada tutulur
├── docker-compose.yml     # Docker servis tanımları
├── Dockerfile             # Uygulama imajı
├── main.py                # Ana uygulama ve zamanlayıcı
├── requirements.txt       # Python bağımlılıkları
└── src/
    └── models/
        └── campground.py  # Kamp alanı veri modeli ve doğrulama
```

---

## Ana Bileşenler ve Fonksiyonlar

### main.py
- **Logger**: Tüm loglar hem terminale hem de `app.log` dosyasına yazılır. Ortam, modül, hata türü ve seviye bilgisi içerir.
- **APScheduler**: Zamanlayıcı ile scraper'ı belirli aralıklarla (örn. 2 dakika) veya cron ile (örn. gece 03:00) çalıştırır.
- **RUN_ON_STARTUP**: ENV değişkeni ile docker başlar başlamaz scraper'ın hemen çalışmasını sağlar.
- **retry_operation**: Tüm kritik işlemler için otomatik retry ve exponential backoff sağlar.
- **handle_exception**: Tüm hata yönetimi merkezi olarak burada yapılır, log seviyeleri ve türleri ayrıdır.
- **init_db**: Veritabanı bağlantısı ve tablo oluşturma işlemlerini yönetir, retry ile güvenli hale getirilmiştir.
- **main**: API'den veri çeker, doğrular ve veritabanına kaydeder. Her çalıştırmada bir defa işini yapar.
- **insert_campground_to_db**: Doğrulanmış kamp alanı verisini veritabanına ekler veya günceller.
- **sanitize_data**: Verileri özel karakterlerden arındırır.

### src/models/campground.py
- **Campground**: Pydantic ile API'den gelen verinin doğrulamasını yapar.
- **CampgroundORM**: SQLAlchemy ile veritabanı modelini tanımlar.
- **prepare_data_for_db**: Doğrulanmış veriyi veritabanına uygun formata çevirir.

---

## Hata Yönetimi ve Loglama
- Tüm hatalar (HTTP, veritabanı, doğrulama, veri tipi, bilinmeyen) `handle_exception` fonksiyonu ile merkezi olarak yönetilir.
- Loglar hem terminalde hem de `app.log` dosyasında detaylı şekilde tutulur.
- Her logda ortam, modül, hata türü ve seviye bilgisi bulunur.

---

## Zamanlama Mantığı
- APScheduler ile scraper belirli aralıklarla veya cron ifadesiyle çalışır.
- Docker konteyneri sürekli açık kalır, zamanlayıcı arka planda bekler.
- Kodun başında zamanlayıcı başlatılır, belirlenen zamanda scraper tetiklenir.
- `RUN_ON_STARTUP=true` ile başlatırsan, docker başlar başlamaz scraper hemen çalışır.

---

## Geliştirici Notları
- Kodda sonsuz döngü yoktur, scraper her tetiklenmede bir defa işini yapar.
- Zamanlama aralığını test için kısa (örn. 2 dakika), prod için cron (örn. gece 03:00) olarak ayarlayabilirsin.
- Tüm loglar sadece `app.log` dosyasında ve terminalde tutulur, başka log dosyası yoktur.
- ENV değişkenleri ile davranış kontrolü sağlanır.

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
tail -f app.log
```

---

## Sıkça Sorulanlar

- **Konteyner kapalıysa cron çalışır mı?**
  - Hayır, konteyner açık olmalı. Zamanlayıcı arka planda bekler.
- **Zamanlamayı nasıl değiştiririm?**
  - `main.py` içinde APScheduler satırında aralığı veya cron ifadesini değiştir.
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
