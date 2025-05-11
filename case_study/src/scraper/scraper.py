import requests
from pydantic import ValidationError
from src.db.base import get_session
from src.db.db import insert_campground_to_db, init_db
from src.models.campground import Campground
from src.logger import logger, ValidationException, handle_exception
from src.config import API_URL
from src.utils.utils import retry_operation, sanitize_data


def http_get_with_retry(url, max_retries=5, timeout=10):
    def op():
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response
    from requests.exceptions import HTTPError, Timeout, ConnectionError, RequestException
    return retry_operation(
        op,
        max_retries=max_retries,
        initial_wait=2,
        backoff_factor=2,
        exception_types=(HTTPError, Timeout, ConnectionError, RequestException),
        context=f"HTTP GET {url}"
    )

def run_scraper_job():
    import time
    start_time = time.time()
    try:
        init_db()
        session = get_session()
        response = http_get_with_retry(API_URL)
        logger.info(f"API yanıt kodu: {response.status_code}", extra={"component": "scraper_module", "function": "run_scraper_job"})
        data = response.json()
        total_count = data.get("meta", {}).get("total_count", len(data.get("data", [])))
        logger.info(f"API'de mevcut toplam kamp alanı sayısı: {total_count}", extra={"component": "scraper_module", "function": "run_scraper_job"})
        locations = data.get("data", [])
        if not locations:
            logger.warning("Hiç kamp alanı bulunamadı.", extra={"component": "scraper_module", "function": "run_scraper_job"})
            return
        for index, location in enumerate(locations, start=1):
            kamp_adi = location.get("attributes", {}).get("name", "Bilinmeyen İsim")
            kamp_adi = sanitize_data(kamp_adi)
            logger.info(f"{index}. --- Kamp alanı işleniyor: {kamp_adi} ---", extra={"component": "scraper_module", "function": "run_scraper_job"})
            raw_data = {
                "id": location.get("id"),
                "type": location.get("type"),
                "links": location.get("links", {}),
                **location.get("attributes", {}),
                "index": index
            }
            raw_data = sanitize_data(raw_data)
            try:
                logger.info("Adım 1: Ham veri doğrulanıyor...", extra={"component": "scraper_module", "function": "run_scraper_job"})
                validated_campground = Campground.validate_api_data(raw_data)
                logger.info("Adım 2: Doğrulama başarılı.", extra={"component": "scraper_module", "function": "run_scraper_job"})
                logger.info("Adım 3: Veritabanına kaydediliyor...", extra={"component": "scraper_module", "function": "run_scraper_job"})
                insert_campground_to_db(session, validated_campground)
            except ValidationError as ve:
                handle_exception(ValidationException(str(ve)), context=f"Kamp alanı: {kamp_adi}", extra_args={"function": "run_scraper_job"})
            except Exception as e:
                handle_exception(e, context=f"Kamp alanı: {kamp_adi}", extra_args={"function": "run_scraper_job"})
        logger.info("Tüm kamp alanları işlendi.", extra={"component": "scraper_module", "function": "run_scraper_job"})
        logger.info(f"{len(locations)} kamp alanı işlendi.", extra={"component": "scraper_module", "function": "run_scraper_job"})
    except Exception as e:
        handle_exception(e, context="Ana döngü", extra_args={"function": "run_scraper_job"})
    finally:
        try:
            session.close()
        except Exception:
            pass
        execution_time = time.time() - start_time
        logger.info(f"Execution Time: {execution_time:.2f} saniye", extra={"component": "scraper_module", "function": "run_scraper_job"})
