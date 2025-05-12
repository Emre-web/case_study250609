# Case Study: FastAPI Scraper & Job Monitor

## Project Overview

This project is a Python-based web scraping application built with **FastAPI**. It\'s designed to periodically fetch data from a specific API endpoint that provides information about campgrounds. Currently, the scraper is configured to retrieve data from a **single, predetermined map location** via the API.

The application leverages FastAPI to provide a robust backend and a simple HTML/JavaScript frontend for user interaction.

Key features include:

-   **FastAPI Backend**: Serves a web interface and provides API endpoints to manage, trigger, and monitor scraping jobs.
    ![Uygulama Arayüzü](static/images/id1.png)
-   **Interactive Frontend**: A user-friendly interface built with HTML and JavaScript (served via `/static/index.html`) allows users to:
    -   Manually trigger the scraper.
    -   View a list of all current and past scraping jobs and their statuses.
    -   Query the detailed status of specific jobs using their unique Job ID.
    -   Receive live (polling-based) updates on job statuses.
-   **Data Scraping & Validation**: Fetches campground data, validates it using Pydantic models.
-   **Database Integration**: Stores validated data in a PostgreSQL database using SQLAlchemy ORM.
-   **Scheduled Jobs**: Utilizes APScheduler to automate the scraping process at regular intervals (e.g., daily at 03:00 and/or every 2 minutes, configurable in `src/main.py`).
-   **Robust Logging**: Implements comprehensive logging in JSON format, capturing detailed information about operations, errors, and system status. All logs are centralized in `logs/app.log` (and also accessible via Docker container logs).
-   **Centralized Error Handling**: Features a robust error handling mechanism for network issues, data parsing problems, timeouts, validation errors, and database transaction failures, with detailed logging.
-   **Dockerized Environment**: Fully containerized with Docker and Docker Compose for easy setup, deployment, and consistent operation across different environments.

## Project Goals

-   To build a reliable and maintainable data scraping pipeline with a user-friendly control interface.
-   To showcase proficiency in FastAPI, Pydantic, SQLAlchemy, APScheduler, Docker, and creating interactive web frontends.
-   To implement best practices in logging, error handling, API design, and application structure.

---

## Key Technologies & Features

-   **Backend**: Python, **FastAPI**
-   **Frontend**: HTML, JavaScript (served statically by FastAPI)
-   **API Interaction (Client-Side)**: `fetch` API in JavaScript
-   **API Interaction (Server-Side Scraper)**: `requests` library (or `httpx` if used) with retry mechanisms.
-   **Data Handling**: Pydantic (validation), SQLAlchemy (ORM)
-   **Database**: PostgreSQL
-   **Scheduling**: APScheduler (integrated within the FastAPI application lifecycle)
-   **Containerization**: Docker, Docker Compose
-   **Logging**: Standard Python `logging` module with JSON Formatter (e.g., `python-json-logger`).
-   **Error Management**: Custom exceptions and a centralized handler (`src/utils/logger.py`).
-   **Concurrency**: FastAPI\'s `async/await` and `BackgroundTasks` for non-blocking operations. `run_in_threadpool` for running synchronous scraper code in an async context.
-   **Current Data Scope**: The scraper currently targets a **single, hardcoded map location** from the API.

---

## Klasör ve Dosya Yapısı

```
case_study/
├── .env                   # Ortam değişkenleri (veritabanı bağlantısı vb. - git'e eklenmemeli)
├── .gitignore             # Git tarafından izlenmeyecek dosyalar
├── Dockerfile             # Uygulama için Docker imajı oluşturma talimatları
├── docker-compose.yml     # Docker servislerini (uygulama, veritabanı) tanımlar
├── requirements.txt       # Python bağımlılıkları
├── README.md              # Bu dosya - proje açıklaması
├── src/                   # Ana uygulama kaynak kodu
│   ├── main.py            # FastAPI uygulaması, API endpointleri, APScheduler yapılandırması
│   ├── config.py          # (Varsa) Uygulama ayarları ve konfigürasyon
│   ├── db/
│   │   ├── base.py        # SQLAlchemy base ve engine kurulumu
│   │   ├── db.py          # Veritabanı CRUD işlemleri, session yönetimi
│   │   └── models.py      # SQLAlchemy ORM modelleri (örn: CampgroundORM)
│   ├── models/
│   │   └── campground.py  # Pydantic veri modelleri (örn: Campground)
│   ├── scraper/
│   │   ├── scraper.py     # API'den veri çekme ve işleme mantığı (run_scraper_job)
│   │   └── scheduler.py   # APScheduler fonksiyonları (artık src/main.py içinde)
│   ├── utils/
│   │   ├── logger.py      # Loglama yapılandırması ve özel hata yönetimi
│   │   └── utils.py       # Yardımcı fonksiyonlar (retry_operation, sanitize_data vb.)
│   └── api/
│       └── endpoints.py   # (Opsiyonel/Kullanılmıyor olabilir) Gelecekteki API modülleri için ayrılmış olabilir. Ana endpointler src/main.py'de.
├── static/                # FastAPI tarafından sunulan statik dosyalar
│   ├── index.html         # Ana kullanıcı arayüzü HTML dosyası
│   └── images/            # (Varsa) Arayüzde kullanılan resimler
│       └── your_image.png # Örnek resim dosyası
└── logs/
    └── app.log            # Uygulama logları (JSON formatında)
```

*Not: `app.log` dosyası hem kök dizinde hem de `logs/` altında olabilir, bu Docker volume mount ayarlarına ve loglama yapılandırmasına bağlıdır. Genellikle tek bir yerde merkezileştirilir (`logs/app.log`).*

---

## Kullanıcı Arayüzü ve API Endpointleri

Uygulama, geliştirme ortamında lokal olarak çalıştırıldığında veya Docker kullanılarak çalıştırıldığında http://localhost:8000 adresinden erişilebilen bir web arayüzü sunar.

### Arayüz İşlevleri (`static/index.html`)

-   **Scraper\'ı Başlat**: "Scraper\'ı Şimdi Çalıştır" butonu ile veri çekme işlemi manuel olarak tetiklenebilir.
-   **Tüm İşleri Listele**: "Tüm İş Durumlarını Getir" butonu ile zamanlanmış ve manuel olarak başlatılmış tüm işlerin listesi ve mevcut durumları görüntülenebilir.
-   **Belirli Bir İşi Sorgula**: Bir "İş ID\'si" girilip "İş Durumunu Sorgula" butonu ile o işe ait detaylı durum bilgileri alınabilir.
-   **Durum Güncellemeleri**: Arayüz, periyodik olarak iş durumlarını sorgulayarak (polling) canlı güncellemeler sunmaya çalışır.

### Ana API Endpointleri (`src/main.py`)

-   `GET /`:
    -   Açıklama: Kullanıcı arayüzünü (`static/index.html`) sunar.
    -   Tarayıcıdan `http://localhost:8000` adresine gidildiğinde otomatik olarak çağrılır.
-   `POST /scrape/start`:
    -   Açıklama: Yeni bir scraper işini arka planda manuel olarak başlatır.
    -   Dönüş: Başarılı olursa bir `job_id` ve mesaj içeren bir JSON nesnesi.
    -   Arayüzdeki "Scraper\'ı Şimdi Çalıştır" butonu bu endpoint\'i kullanır.
-   `GET /scrape/status`:
    -   Açıklama: Tüm scraper işlerinin (manuel ve zamanlanmış) mevcut durumlarını ve detaylarını listeler.
    -   Dönüş: İş ID\'lerini anahtar olarak kullanan ve her bir işin durumunu içeren bir JSON nesnesi.
    -   Arayüzdeki "Tüm İş Durumlarını Getir" butonu ve periyodik durum güncellemeleri bu endpoint\'i kullanır.
-   `GET /scrape/status/{job_id}`:
    -   Açıklama: `{job_id}` ile belirtilen spesifik bir scraper işinin detaylı durumunu döndürür.
    -   Dönüş: İlgili işin durumunu ve detaylarını içeren bir JSON nesnesi veya iş bulunamazsa 404 hatası.
    -   Arayüzdeki "İş Durumunu Sorgula" özelliği bu endpoint\'i kullanır.
-   `GET /static/...`:
    -   Açıklama: `static` klasörü içindeki dosyaları (HTML, CSS, JavaScript, resimler) sunar.

---

## Kurulum ve Çalıştırma

### Gereksinimler

-   Docker ve Docker Compose
-   (Geliştirme için) Python 3.8+ ve pip

### Hızlı Başlangıç

#### 1. Docker ile Çalıştırma

Projenin kök dizininde aşağıdaki komutu çalıştırın:

```sh
docker compose up --build
```

-   Bu komut, gerekli Docker imajlarını oluşturur (veya günceller) ve `scraper` (uygulama) ile `db` (PostgreSQL veritabanı) servislerini başlatır.
-   Uygulama, `http://localhost:8000` adresinde erişilebilir bir FastAPI arayüzü ile başlar. Bu arayüz üzerinden scraper manuel olarak tetiklenebilir ve iş durumları izlenebilir.
-   APScheduler ile tanımlanmış zamanlanmış görevler (örn: her gün 03:00'da) otomatik olarak çalışır.
-   Tüm loglar `logs/app.log` dosyasına JSON formatında yazılır ve `docker compose logs scraper` komutu ile de görüntülenebilir.

#### 2. Scraper\'ı Hemen Çalıştırmak İçin (Docker ile)

Eğer uygulamayı başlatır başlatmaz bir scraper görevinin hemen çalışmasını istiyorsanız (zamanlayıcıyı beklemeden), `docker-compose.yml` dosyasında `scraper` servisinin `environment` bölümüne `RUN_ON_STARTUP=true` ekleyebilir veya komutu şu şekilde çalıştırabilirsiniz:

```sh
docker compose run -e RUN_ON_STARTUP=true scraper_service_name
```

*(Not: `scraper_service_name` yerine `docker-compose.yml` dosyanızdaki servis adını yazın, genellikle `scraper` veya `app` olabilir.)*
-   Bu şekilde başlatırsanız, scraper Docker konteyneri başlar başlamaz hemen çalışır, ardından zamanlayıcı ile otomatik çalışmaya devam eder. (Bu özellik `src/main.py` içinde `RUN_ON_STARTUP` ortam değişkenine göre yönetiliyorsa geçerlidir.)

#### 3. Geliştirici Modunda (Lokal)

Lokal makinenizde Docker olmadan geliştirmek ve çalıştırmak için:

1.  **Sanal Ortam Oluşturun ve Aktifleştirin (Önerilir):**
    ```sh
    python -m venv venv
    source venv/bin/activate  # Linux/macOS için
    # venv\Scripts\activate    # Windows için
    ```

2.  **Bağımlılıkları Yükleyin:**
    Projenin kök dizinindeyken:
    ```sh
    pip install -r requirements.txt
    ```

3.  **(Opsiyonel) `.env` Dosyası Oluşturun:**
    Projenin kök dizininde `.env` adında bir dosya oluşturarak veritabanı bağlantı bilgileri gibi ortam değişkenlerini tanımlayın. Örnek:
    ```env
    DATABASE_URL=postgresql://user:password@localhost:5432/campgrounds_db
    # Diğer ayarlar...
    ```
    `src/config.py` veya `src/main.py` bu değişkenleri okuyacak şekilde ayarlanmalıdır (örn: `python-dotenv` kütüphanesi ile).

4.  **PostgreSQL Veritabanını Çalıştırın:**
    Lokalinizde çalışan bir PostgreSQL sunucusuna ihtiyacınız olacak. Docker ile sadece veritabanını da başlatabilirsiniz:
    ```sh
    docker compose up -d db
    ```
    Bu, `docker-compose.yml` dosyasındaki `db` servisini arka planda başlatır.

5.  **FastAPI Uygulamasını Uvicorn ile Çalıştırın:**
    Projenin kök dizinindeyken:
    ```sh
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
    ```
    -   `--reload`: Kodda değişiklik yaptığınızda sunucunun otomatik olarak yeniden başlatılmasını sağlar.
    -   Uygulama web arayüzüne `http://localhost:8000` adresinden erişilebilir olacaktır.

Eğer sadece zamanlanmış scraper görevini (FastAPI sunucusu olmadan, genellikle test veya basit senaryolar için) çalıştırmak isterseniz ve `src/main.py` dosyanızda `if __name__ == "__main__":` bloğu altında böyle bir mantık varsa:
```sh
python src/main.py
```
Ancak, FastAPI ile entegre bir APScheduler için genellikle `uvicorn` ile çalıştırmak standarttır.

---

## Loglama Sistemi

-   Tüm loglar JSON formatında, genellikle `logs/app.log` dosyasına yazılır.
-   Docker kullanılıyorsa, loglar `docker compose logs scraper_service_name` komutuyla da görüntülenebilir.
-   Log seviyeleri: DEBUG, INFO, WARNING, ERROR, CRITICAL.
-   Her log kaydı şunları içerir: zaman damgası, log seviyesi, logu üreten modül/fonksiyon adı, hata türü (`errtype` anahtarı ile özel olarak tanımlanmışsa), ana mesaj ve (varsa) exception detayları.
-   Örnek hata türleri (`errtype`): `NETWORK_ERROR`, `DATA_PARSE_ERROR`, `TIMEOUT_ERROR`, `INVALID_DATA_ERROR`, `VALIDATION_ERROR`, `DB_ERROR`, `HTTP_ERROR`, `GENERIC_ERROR`, `NO_ERROR` (başarılı işlemler için).

---

## Ana Fonksiyonlar ve Modüller (Özet)

-   **`src/main.py`**:
    -   FastAPI uygulamasının ana giriş noktası.
    -   API endpoint\'lerini tanımlar (`/scrape/start`, `/scrape/status` vb.).
    -   Statik dosyaları (`static/index.html`) sunar.
    -   APScheduler\'ı yapılandırır ve FastAPI uygulama yaşam döngüsü (`lifespan` context manager) ile entegre eder.
    -   İş durumlarını (`job_statuses`) yönetir.
-   **`src/scraper/scraper.py` (`run_scraper_job` fonksiyonu)**:
    -   Asıl veri çekme, işleme ve veritabanına kaydetme mantığını içerir.
    -   API isteklerini yapar, veriyi Pydantic modelleri ile doğrular ve SQLAlchemy aracılığıyla veritabanına yazar.
-   **`src/db/db.py` ve `src/db/models.py`**:
    -   Veritabanı bağlantısı (`init_db`), session yönetimi ve SQLAlchemy ORM modellerini içerir.
-   **`src/models/campground.py`**:
    -   API\'den gelen veri için Pydantic doğrulama modellerini tanımlar.
-   **`src/utils/logger.py`**:
    -   JSON formatında loglama yapılandırmasını ve `handle_exception` gibi merkezi hata loglama fonksiyonlarını sağlar.
-   **`src/utils/utils.py`**:
    -   `retry_operation` gibi genel yardımcı fonksiyonları içerebilir.

---

## Hata Yönetimi ve Loglama

-   Tüm beklenen ve beklenmeyen hatalar, özellikle `run_scraper_job` içinde `try-except` blokları ile yakalanır.
-   Yakalanan hatalar, `src/utils/logger.py` içindeki `handle_exception` benzeri bir fonksiyon aracılığıyla veya doğrudan logger kullanılarak detaylı bir şekilde loglanır.
-   Loglarda fonksiyon adı, hata türü (`errtype`) ve hata mesajı açıkça belirtilir.
-   Başarılı operasyonlar da genellikle `INFO` seviyesinde, `errtype: NO_ERROR` ile loglanır.
-   FastAPI endpoint\'lerinde oluşan hatalar, standart HTTP hata kodları (örn: 404, 500) ve açıklayıcı JSON yanıtları ile istemciye bildirilir.

---

## Sık Kullanılan Komutlar

**Standart Başlatma (Docker ile):**
```sh
docker compose up --build
```
(Uygulamaya `http://localhost:8000` adresinden erişin.)

**Logları Görmek (Docker ile):**
```sh
docker compose logs -f scraper_service_name
```
(`scraper_service_name` yerine `docker-compose.yml` dosyanızdaki servis adını yazın.)

**Lokal Geliştirme Sunucusunu Başlatma:**
```sh
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Sıkça Sorulanlar

-   **Konteyner kapalıysa zamanlanmış (cron) işler çalışır mı?**
    -   Hayır, FastAPI uygulamasını (ve dolayısıyla APScheduler\'ı) barındıran Docker konteyneri çalışır durumda olmalıdır.
-   **Zamanlamayı nasıl değiştiririm?**
    -   `src/main.py` dosyasındaki APScheduler yapılandırmasında (`scheduler.add_job` içindeki `CronTrigger` veya `IntervalTrigger` parametrelerini) düzenleyerek.
-   **Veritabanı bağlantısı veya HTTP hatalarında ne olur?**
    -   Uygulama, bu tür hataları yakalamak ve loglamak için tasarlanmıştır. `src/utils/utils.py` içindeki `retry_operation` gibi mekanizmalar, geçici ağ sorunlarına karşı direnç sağlayabilir. Tüm kritik hatalar `logs/app.log` dosyasına detaylı olarak yazılır.

---

## Katkı ve Geliştirme

-   Kodun PEP8 standartlarına uygun ve sürdürülebilir olmasına özen gösterilmiştir.
-   Yeni özellikler veya endpoint\'ler eklerken, mevcut merkezi hata yönetimi ve loglama yapısını kullanmaya devam edin.
-   APScheduler ile yeni zamanlanmış görevler ekleyecekseniz, `src/main.py` içindeki `lifespan` fonksiyonunu inceleyin.
-   Ortam değişkenlerini (`.env` dosyası ve `src/config.py` aracılığıyla) kullanarak yapılandırmayı yönetin.

---

## İletişim

Her türlü soru, öneri ve katkı için proje sahibiyle iletişime geçebilirsiniz.
