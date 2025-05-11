# -*- coding: utf-8 -*-
from src.scraper.scheduler import start_scheduler
from src.config import RUN_ON_STARTUP
from src.scraper import run_scraper_job
from src.logger import logger

if __name__ == "__main__":
    scheduler = start_scheduler()
    logger.info("APScheduler başlatıldı. Scraper her 2 dakikada bir çalışacak.")
    if RUN_ON_STARTUP:
        logger.info("RUN_ON_STARTUP=true, scraper hemen başlatılıyor.")
        run_scraper_job()
    try:
        while True:
            import time
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
