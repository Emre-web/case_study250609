import logging
import sys
import json
import os
import time
from logging.handlers import RotatingFileHandler
from src.config import ENV

class JsonFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%', validate=True, *, defaults=None):
        # Pass datefmt to the superclass constructor
        super().__init__(fmt=fmt, datefmt=datefmt, style=style, validate=validate, defaults=defaults)

    def format(self, record):
        # Use self.datefmt if set by constructor, otherwise default strftime for timestamp
        timestamp_str = self.formatTime(record, self.datefmt) 
        
        log_record = {
            "timestamp": timestamp_str,
            "record_date": time.strftime("%Y-%m-%d", time.localtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "env": getattr(record, "env", ENV),
            "module": record.module,
            "component": getattr(record, "component", None),
            "function": getattr(record, "function", None),
            "errtype": getattr(record, "errtype", "GENERIC"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record, ensure_ascii=False)

# --- Directory Setup ---
LOG_ROOT_DIR = "logs"
ARCHIVE_LOG_DIR = os.path.join(LOG_ROOT_DIR, "archive")

if not os.path.exists(LOG_ROOT_DIR):
    os.makedirs(LOG_ROOT_DIR)
if not os.path.exists(ARCHIVE_LOG_DIR):
    os.makedirs(ARCHIVE_LOG_DIR)

# --- Logger Instance ---
logger = logging.getLogger("case_study")
logger.setLevel(logging.DEBUG)

# --- Custom Rotator for app.log Archiving ---
def archive_rotator(source, dest_unused):
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    archive_path = os.path.join(ARCHIVE_LOG_DIR, f"app.log.{timestamp}")
    if os.path.exists(source):
        try:
            os.rename(source, archive_path)
        except Exception as e:
            print(f"Error during app.log rotation: {e}", file=sys.stderr)

# --- Standard Namer for RotatingFileHandler backups (e.g., .1, .2) ---
def default_namer(name):
    return name + ".old"

# --- Handlers Setup ---
JSON_DATEFMT = '%Y-%m-%d %H:%M:%S,%03d'

# 1. Daily Summary Log Handler (logs/daily_summary.json)
summary_log_filepath = os.path.join(LOG_ROOT_DIR, "daily_summary.json")
summary_file_handler = RotatingFileHandler(
    summary_log_filepath,
    maxBytes=20*1024*1024,  # 20 MB
    backupCount=3,          # Keeps daily_summary.json.1, .2, .3
    encoding="utf-8",
    delay=True
)
summary_file_handler.setFormatter(JsonFormatter(datefmt=JSON_DATEFMT))
summary_file_handler.setLevel(logging.DEBUG)

# 2. Main App Log Handler with Archiving (logs/app.log)
app_log_filepath = os.path.join(LOG_ROOT_DIR, "app.log")
app_log_handler = RotatingFileHandler(
    app_log_filepath,
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=0,          # Archiving handled by custom rotator
    encoding="utf-8",
    delay=True
)
app_log_handler.rotator = archive_rotator
# app_log_handler.namer = default_namer # Not strictly needed if backupCount is 0
app_log_handler.setFormatter(JsonFormatter(datefmt=JSON_DATEFMT))
app_log_handler.setLevel(logging.DEBUG)

# 3. Console Handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(JsonFormatter(datefmt=JSON_DATEFMT))
console_handler.setLevel(logging.INFO)

# Clear existing handlers and add new ones
if logger.hasHandlers():
    logger.handlers.clear()

logger.addHandler(summary_file_handler) # New summary handler
logger.addHandler(app_log_handler)
logger.addHandler(console_handler)

# --- Custom Exception Classes ---
class DatabaseException(Exception): pass
class ValidationException(Exception): pass

# --- Exception Handling Function ---
# Assuming requests.exceptions are imported where this handler is called or here
from requests.exceptions import HTTPError, Timeout, ConnectionError

def handle_exception(exc, context=None, extra_args=None):
    component_name = context if context else "main"
    extra_info = {"component": component_name}
    if extra_args: # Merge extra_args if provided
        extra_info.update(extra_args)

    if isinstance(exc, HTTPError):
        extra_info["errtype"] = "HTTP_ERROR"
        logger.error(f"HTTP Hatası: {exc.response.status_code if exc.response else 'Unknown Status Code'}", extra=extra_info)
    elif isinstance(exc, Timeout):
        extra_info["errtype"] = "HTTP_TIMEOUT"
        logger.error(f"Timeout Hatası: {exc}", extra=extra_info)
    elif isinstance(exc, ConnectionError):
        extra_info["errtype"] = "HTTP_CONNECTION"
        logger.error(f"Bağlantı Hatası: {exc}", extra=extra_info)
    elif isinstance(exc, ValidationException):
        extra_info["errtype"] = "VALIDATION_ERROR"
        logger.warning(f"Doğrulama Hatası: {exc}", extra=extra_info)
    elif isinstance(exc, DatabaseException):
        extra_info["errtype"] = "DATABASE_ERROR"
        logger.critical(f"Veritabanı Hatası: {exc}", extra=extra_info)
    elif isinstance(exc, ValueError):
        extra_info["errtype"] = "VALUE_ERROR"
        logger.error(f"Değer Hatası: {exc}", extra=extra_info)
    else:
        extra_info["errtype"] = "GENERIC_UNHANDLED_ERROR"
        logger.exception(f"Bilinmeyen Bir Hata Oluştu ({type(exc).__name__}): {exc}", extra=extra_info)
