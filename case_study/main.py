# -*- coding: utf-8 -*-
from src.scraper.scheduler import start_scheduler
from src.config import RUN_ON_STARTUP
from src.scraper import run_scraper_job
from src.logger import logger

if __name__ == "__main__":
    scheduler = start_scheduler()
    logger.info("APScheduler başlatıldı. Scraper her 2 dakikada bir çalışacak.", extra={"component": "main_app", "function": "main_runtime"})

    # Eğer RUN_ON_STARTUP true ise scraper hemen başlatılır. bunu sağlamak için
    # config.py dosyasında RUN_ON_STARTUP değişkenini true yapmalısınız.
    # Bu, scraper'ın hemen çalışmasını sağlar.
    if RUN_ON_STARTUP:
        logger.info("RUN_ON_STARTUP=true, scraper hemen başlatılıyor.", extra={"component": "main_app", "function": "initial_run"})
        run_scraper_job()
    try:
        while True:
            import time
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
