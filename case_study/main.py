# -*- coding: utf-8 -*-
import requests
import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, JSON, DateTime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import inspect
from src.models.campground import Base, Campground, CampgroundORM
from pydantic import ValidationError
import html
import time
import os
import sys
import logging
from requests.exceptions import RequestException, HTTPError, Timeout, ConnectionError
from apscheduler.schedulers.background import BackgroundScheduler

DATABASE_URL = "postgresql://user:password@postgres:5432/case_study"

# Ortam (dev/stage/prod) bilgisini ENV ile al
ENV = os.getenv("ENV", "dev")

# Logger ayarları
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Dosya handler
file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(env)s | %(module)s | %(errtype)s | %(message)s"
)
file_handler.setFormatter(file_formatter)

# Konsol handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(env)s | %(module)s | %(errtype)s | %(message)s"
)
console_handler.setFormatter(console_formatter)

# Çift logu önlemek için eski handlerları temizle
if logger.hasHandlers():
    logger.handlers.clear()

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Log kaydında ortam, modül ve hata türü için ekstra bilgiler ekle
class ContextFilter(logging.Filter):
    def filter(self, record):
        record.env = ENV
        record.errtype = getattr(record, "errtype", "GENERIC")
        return True
logger.addFilter(ContextFilter())

class DatabaseException(Exception):
    pass

class ValidationException(Exception):
    pass

def handle_exception(exc, context=None):
    """
    Tüm hata yönetimi buradan geçer. Exception türüne göre loglar ve gerekirse raise eder.
    """
    module = context if context else "main"
    if isinstance(exc, HTTPError):
        logger.error(f"HTTP Hatası: {exc}", extra={"module": module, "errtype": "HTTP"})
    elif isinstance(exc, Timeout):
        logger.error(f"Timeout Hatası: {exc}", extra={"module": module, "errtype": "HTTP"})
    elif isinstance(exc, ConnectionError):
        logger.error(f"Bağlantı Hatası: {exc}", extra={"module": module, "errtype": "HTTP"})
    elif isinstance(exc, ValidationException):
        logger.warning(f"Doğrulama Hatası: {exc}", extra={"module": module, "errtype": "VALIDATION"})
    elif isinstance(exc, DatabaseException):
        logger.critical(f"Veritabanı Hatası: {exc}", extra={"module": module, "errtype": "DB"})
    elif isinstance(exc, ValueError):
        logger.error(f"Veri Tipi Hatası: {exc}", extra={"module": module, "errtype": "TYPE"})
    else:
        logger.exception(f"Bilinmeyen Hata: {exc}", extra={"module": module, "errtype": "GENERIC"})

def retry_operation(operation, max_retries=5, initial_wait=2, backoff_factor=2, exception_types=(Exception,), context=None):
    """
    Genel amaçlı retry mekanizması. Belirtilen exception türlerinde otomatik tekrar dener.
    """
    wait = initial_wait
    for attempt in range(1, max_retries + 1):
        try:
            return operation()
        except exception_types as exc:
            handle_exception(exc, context=f"{context}, attempt {attempt}")
            if attempt == max_retries:
                raise
            time.sleep(wait)
            wait *= backoff_factor

def http_get_with_retry(url, max_retries=5, timeout=10):
    """
    HTTP GET isteği yapar, hata durumunda otomatik olarak tekrar dener.
    """
    def op():
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response
    return retry_operation(
        op,
        max_retries=max_retries,
        initial_wait=2,
        backoff_factor=2,
        exception_types=(HTTPError, Timeout, ConnectionError, RequestException),
        context=f"HTTP GET {url}"
    )

def init_db():
    """
    Veritabanını başlatır ve tabloları oluşturur (eğer yoksa).
    Veritabanı hazır değilse bağlantıyı tekrar dener.
    """
    def op():
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)
        if not inspector.has_table("campgrounds"):
            Base.metadata.create_all(engine)
            logger.info("Veritabanı başlatıldı ve tablolar oluşturuldu.")
        else:
            logger.info("Veritabanı zaten başlatılmış. Tablo oluşturma atlanıyor.")
        return True
    try:
        retry_operation(
            op,
            max_retries=5,
            initial_wait=3,
            backoff_factor=2,
            exception_types=(Exception,),
            context="init_db"
        )
    except Exception:
        raise DatabaseException("Birden fazla denemeden sonra veritabanına bağlanılamadı.")

def sanitize_data(data):
    """
    Verileri özel karakterlerden arındırır.
    """
    if isinstance(data, str):
        return html.escape(data)
    elif isinstance(data, dict):
        return {key: sanitize_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    return data

def insert_campground_to_db(session, validated_campground):
    """
    Doğrulanmış kamp alanı verilerini veritabanına ekler.
    Eğer kayıt zaten varsa, dinamik olarak tüm sütunları günceller.
    """
    try:
        db_data = CampgroundORM.prepare_data_for_db(validated_campground)
        db_data = sanitize_data(db_data)

        existing_campground = session.query(CampgroundORM).filter_by(id=db_data["id"]).first()

        if existing_campground:
            logger.info(f"Kamp alanı zaten mevcut. Kayıt güncelleniyor: {validated_campground.name}")
            for key, value in db_data.items():
                if hasattr(existing_campground, key):
                    setattr(existing_campground, key, value)
            logger.info(f"Kamp alanı başarıyla güncellendi: {validated_campground.name}")
        else:
            logger.info(f"Kamp alanı mevcut değil. Yeni kayıt ekleniyor: {validated_campground.name}")
            new_campground = CampgroundORM(**db_data)
            session.add(new_campground)
            logger.info(f"Yeni kamp alanı başarıyla eklendi: {validated_campground.name}")

        session.commit()
    except Exception as e:
        session.rollback()
        handle_exception(DatabaseException(str(e)), context=f"insert_campground_to_db: {validated_campground.name}")

def main():
    """
    Kamp alanı verilerini çekip, doğrulayıp, veritabanına kaydeder.
    """
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    url = "https://thedyrt.com/api/v6/locations/search-results?filter%5Bsearch%5D%5Bdrive_time%5D=any&filter%5Bsearch%5D%5Bair_quality%5D=any&filter%5Bsearch%5D%5Belectric_amperage%5D=any&filter%5Bsearch%5D%5Bmax_vehicle_length%5D=any&filter%5Bsearch%5D%5Bprice%5D=any&filter%5Bsearch%5D%5Brating%5D=any&filter%5Bsearch%5D%5Bbbox%5D=-118.001%2C24.942%2C-77.63%2C50.061&sort=recommended&page%5Bnumber%5D=1&page%5Bsize%5D=500"

    try:
        response = http_get_with_retry(url)
        data = response.json()

        total_count = data.get("meta", {}).get("total_count", len(data.get("data", [])))
        logger.info(f"API'de mevcut toplam kamp alanı sayısı: {total_count}")

        locations = data.get("data", [])

        if not locations:
            logger.warning("Hiç kamp alanı bulunamadı.")
            return

        existing_ids = {campground.id for campground in session.query(CampgroundORM.id).all()}

        for index, location in enumerate(locations, start=1):
            kamp_adi = location.get("attributes", {}).get("name", "Bilinmeyen İsim")
            kamp_adi = sanitize_data(kamp_adi)
            logger.info(f"{index}. --- Kamp alanı işleniyor: {kamp_adi} ---")

            raw_data = {
                "id": location.get("id"),
                "type": location.get("type"),
                "links": location.get("links", {}),
                **location.get("attributes", {}),
                "index": index
            }
            raw_data = sanitize_data(raw_data)

            try:
                logger.info("Adım 1: Ham veri doğrulanıyor...")
                validated_campground = Campground.validate_api_data(raw_data)
                logger.info("Adım 2: Doğrulama başarılı.")

                logger.info("Adım 3: Veritabanına kaydediliyor...")
                insert_campground_to_db(session, validated_campground)

            except ValidationError as ve:
                handle_exception(ValidationException(str(ve)), context=f"Kamp alanı: {kamp_adi}")
            except Exception as e:
                handle_exception(e, context=f"Kamp alanı: {kamp_adi}")

        logger.info("Tüm kamp alanları işlendi.")
        logger.info(f"{len(locations)} kamp alanı işlendi.")
    except Exception as e:
        handle_exception(e, context="Ana döngü")
    finally:
        session.close()

def run_scraper_job():
    try:
        init_db()
        main()
    except Exception as e:
        handle_exception(e, context="run_scraper_job")

if __name__ == "__main__":
    # ENV: RUN_ON_STARTUP=true ise başlat, yoksa sadece zamanlayıcı bekler
    RUN_ON_STARTUP = os.getenv("RUN_ON_STARTUP", "false").lower() == "true"
    scheduler = BackgroundScheduler()
    # Her 2 dakikada bir çalışacak şekilde ayarla
    scheduler.add_job(run_scraper_job, 'interval', minutes=2)
    scheduler.start()
    logger.info("APScheduler başlatıldı. Scraper her 2 dakikada bir çalışacak.")
    if RUN_ON_STARTUP:
        logger.info("RUN_ON_STARTUP=true, scraper hemen başlatılıyor.")
        run_scraper_job()
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
