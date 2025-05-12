from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse 
from fastapi.staticfiles import StaticFiles 
from fastapi.concurrency import run_in_threadpool
from contextlib import asynccontextmanager
import uvicorn 
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.triggers.cron import CronTrigger

from src.scraper.scraper import run_scraper_job 
from src.logger import logger 

import uuid
import datetime

# İş durumları için sabitler
JOB_STATUS_PENDING = "PENDING"
JOB_STATUS_RUNNING = "RUNNING"
JOB_STATUS_COMPLETED = "COMPLETED"
JOB_STATUS_FAILED = "FAILED"

# İş durumlarını ve detaylarını saklamak için global bir sözlük
# Daha büyük uygulamalarda Redis gibi harici bir depolama düşünülebilir.
job_statuses = {}

async def _run_scraper_job_with_status(job_id: str, job_name: str):
    logger.info(f"İş başlıyor: {job_name} (ID: {job_id})", extra={"component": "job_runner", "job_id": job_id, "job_name": job_name})
    # Ensure the job_id exists in job_statuses before trying to update it,
    # especially if it's initialized elsewhere or might be cleared.
    if job_id not in job_statuses:
        job_statuses[job_id] = {} # Initialize if not present

    job_statuses[job_id].update({ # Use update to preserve other potential keys like 'type', 'schedule'
        "status": JOB_STATUS_RUNNING,
        "job_name": job_name, # Keep job_name in case it's not already there or needs update
        "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "details": "İş çalışıyor..."
    })
    try:
        # Run the synchronous scraper job in a separate thread pool
        scraper_result = await run_in_threadpool(run_scraper_job) # Dönen değeri al
        
        job_statuses[job_id].update({
            "status": JOB_STATUS_COMPLETED,
            "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "details": scraper_result if scraper_result is not None else "İş başarıyla tamamlandı, ancak ek detay yok." # Sonucu details'e ata
        })
        logger.info(f"İş başarıyla tamamlandı: {job_name} (ID: {job_id})", extra={"component": "job_runner", "job_id": job_id, "job_name": job_name})
    except Exception as e:
        error_message = f"İş sırasında hata oluştu: {str(e)}"
        job_statuses[job_id].update({
            "status": JOB_STATUS_FAILED,
            "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "details": "İş hata ile sonlandı.",
            "error": error_message 
        })
        logger.error(f"İş hata ile sonlandı: {job_name} (ID: {job_id}). Hata: {error_message}", extra={"component": "job_runner", "job_id": job_id, "job_name": job_name}, exc_info=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI uygulaması başlatılıyor.")
    app.state.job_statuses = job_statuses # Global sözlüğü app state'e atayarak endpoint'lerden erişim
    scheduler = AsyncIOScheduler(timezone="Europe/Istanbul", executors={'default': AsyncIOExecutor()})
    
    # Başlangıçta çalışan kazıyıcı kaldırıldı.
    # Günlük cron görevi
    daily_job_id = "scheduled_daily_scraper_0300"
    job_statuses[daily_job_id] = {
        "status": JOB_STATUS_PENDING,
        "job_name": "Günlük Scraper (03:00)",
        "type": "scheduled",
        "schedule": "Her gün 03:00",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "details": "Zamanlanmış görev oluşturuldu, tetiklenmeyi bekliyor."
    }
    scheduler.add_job(
        _run_scraper_job_with_status,
        CronTrigger(hour=3, minute=0, timezone="Europe/Istanbul"),
        args=[daily_job_id, "Günlük Scraper (03:00)"],
        id=daily_job_id, # APScheduler için de aynı ID
        replace_existing=True
    )
    logger.info(f"{job_statuses[daily_job_id]['job_name']} zamanlandı (ID: {daily_job_id}).")
    
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("APScheduler başlatıldı ve görevler zamanlandı.")
    
    yield
    
    logger.info("FastAPI uygulaması kapatılıyor.")
    if hasattr(app.state, 'scheduler') and app.state.scheduler.running:
        app.state.scheduler.shutdown()
        logger.info("APScheduler durduruldu.")

app = FastAPI(lifespan=lifespan)

# Statik dosyalar için mount
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/scrape/start", status_code=202) 
async def start_scraping_job_manual(background_tasks: BackgroundTasks):
    """
    Scraper işlemini manuel olarak arka planda başlatır ve bir iş ID'si döner.
    """
    job_id = f"manual_scraper_{uuid.uuid4()}"
    job_name = "Manuel Scraper"
    logger.info(f"Manuel scraper başlatma isteği alındı. Atanan ID: {job_id}", extra={"component": "api", "function": "start_scraping_job_manual", "job_id": job_id})
    
    app.state.job_statuses[job_id] = {
        "status": JOB_STATUS_PENDING,
        "job_name": job_name,
        "type": "manual",
        "triggered_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "details": "Manuel iş tetiklendi, başlaması bekleniyor."
    }
    
    try:
        background_tasks.add_task(_run_scraper_job_with_status, job_id, job_name)
        message = f"Scraper görevi başarıyla arka planda başlatıldı. İş ID: {job_id}"
        logger.info(message, extra={"component": "api", "function": "start_scraping_job_manual", "job_id": job_id})
        return {"message": message, "job_id": job_id}
    except Exception as e:
        error_message = f"Scraper görevi başlatılırken hata oluştu: {str(e)}"
        # Bu aşamada hata olursa, job_statuses'a PENDING olarak eklenmiş olabilir, FAILED'a çekebiliriz.
        app.state.job_statuses[job_id].update({
            "status": JOB_STATUS_FAILED,
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "details": "İş başlatılamadı.",
            "error": error_message
        })
        logger.error(error_message, extra={"component": "api", "function": "start_scraping_job_manual", "job_id": job_id, "errtype": "API_ERROR"}, exc_info=True)
        # FastAPI'nin default exception handler'ı 500 dönecektir, ancak özel bir yanıt da oluşturulabilir.
        # from fastapi import HTTPException
        # raise HTTPException(status_code=500, detail=error_message)
        # Şimdilik basit bir dönüş yapalım, FastAPI normal hata yönetimini yapsın.
        return {"error": error_message, "job_id": job_id, "status_code": 500}

@app.get("/scrape/status")
async def get_all_job_statuses():
    """
    Tüm scraper işlerinin mevcut durumlarını listeler.
    """
    # logger.info(f"Current job_statuses: {app.state.job_statuses}", extra={"component": "api", "function": "get_all_job_statuses"})
    return app.state.job_statuses

@app.get("/scrape/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Belirli bir scraper işinin durumunu ID ile sorgular.
    """
    if job_id in app.state.job_statuses:
        return app.state.job_statuses[job_id]
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"İş ID'si bulunamadı: {job_id}")

@app.get("/", response_class=FileResponse) 
async def read_root():
    return FileResponse("static/index.html")
    # logger.info("Tüm iş durumları sorgulandı.") # Loglama isteğe bağlı
    if not hasattr(app.state, 'job_statuses') or not app.state.job_statuses:
        return {}
    return app.state.job_statuses

# if __name__ == "__main__":
    # uvicorn.run(app, host="0.0.0.0", port=8000)

