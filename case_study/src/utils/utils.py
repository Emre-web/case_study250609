import time
import html
from src.logger import handle_exception

def retry_operation(operation, max_retries=5, initial_wait=2, backoff_factor=2, exception_types=(Exception,), context=None):
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

def sanitize_data(data):
    if isinstance(data, str):
        return html.escape(data)
    elif isinstance(data, dict):
        return {key: sanitize_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    return data
