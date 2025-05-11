import logging
import sys
import json
from logging.handlers import RotatingFileHandler
from src.config import ENV

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "env": getattr(record, "env", ENV),
            "module": record.module,
            "errtype": getattr(record, "errtype", "GENERIC"),
            "message": record.getMessage(),
            "user_id": getattr(record, "user_id", None),
            "ip": getattr(record, "ip", None),
            "session_id": getattr(record, "session_id", None),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record, ensure_ascii=False)

logger = logging.getLogger("case_study")
logger.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler("app.log", maxBytes=5*1024*1024, backupCount=5, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(JsonFormatter())

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(JsonFormatter())

if logger.hasHandlers():
    logger.handlers.clear()
logger.addHandler(file_handler)
logger.addHandler(console_handler)

class DatabaseException(Exception): pass
class ValidationException(Exception): pass

def handle_exception(exc, context=None):
    module = context if context else "main"
    from requests.exceptions import HTTPError, Timeout, ConnectionError
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
