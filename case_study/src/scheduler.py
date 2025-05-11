from apscheduler.schedulers.background import BackgroundScheduler
from src.scraper import run_scraper_job

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_scraper_job, 'interval', minutes=2)
    scheduler.start()
    return scheduler
