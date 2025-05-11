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
            "function": getattr(record, "function", None),
            "errtype": getattr(record, "errtype", "NO_ERROR"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record, ensure_ascii=False)

logger = logging.getLogger("case_study")
logger.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler("logs/app.log", maxBytes=5*1024*1024, backupCount=5, encoding="utf-8")
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
class NetworkError(Exception): pass
class DataParseError(Exception): pass
class TimeoutError(Exception): pass
class InvalidDataError(Exception): pass

def handle_exception(exc, context=None, func_name=None):
    module = context if context else "main"
    from requests.exceptions import HTTPError, Timeout, ConnectionError
    extra = {"module": module, "function": func_name or "unknown"}
    if isinstance(exc, NetworkError) or isinstance(exc, ConnectionError):
        logger.error(f"NETWORK_ERROR: Ağ bağlantısı hatası: {exc}", extra={**extra, "errtype": "NETWORK_ERROR"})
    elif isinstance(exc, DataParseError):
        logger.error(f"DATA_PARSE_ERROR: Veri ayrıştırma hatası: {exc}", extra={**extra, "errtype": "DATA_PARSE_ERROR"})
    elif isinstance(exc, TimeoutError) or isinstance(exc, Timeout):
        logger.error(f"TIMEOUT_ERROR: Zaman aşımı hatası: {exc}", extra={**extra, "errtype": "TIMEOUT_ERROR"})
    elif isinstance(exc, InvalidDataError):
        logger.error(f"INVALID_DATA_ERROR: Beklenmeyen veri formatı: {exc}", extra={**extra, "errtype": "INVALID_DATA_ERROR"})
    elif isinstance(exc, HTTPError):
        logger.error(f"HTTP Hatası: {exc}", extra={**extra, "errtype": "HTTP"})
    elif isinstance(exc, ValidationException):
        logger.warning(f"Doğrulama Hatası: {exc}", extra={**extra, "errtype": "VALIDATION"})
    elif isinstance(exc, DatabaseException):
        logger.critical(f"Veritabanı Hatası: {exc}", extra={**extra, "errtype": "DB"})
    elif isinstance(exc, ValueError):
        logger.error(f"Veri Tipi Hatası: {exc}", extra={**extra, "errtype": "TYPE"})
    else:
        logger.exception(f"Bilinmeyen Hata: {exc}", extra={**extra, "errtype": "GENERIC"})
