import time
import logging
import functools

logger = logging.getLogger(__name__)

def retry_on_transient_error(max_retries=3, initial_delay=1.0, backoff_factor=2.0):
    """Decorator to retry API calls on transient errors (connection, timeouts, rate limits) with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exc = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    exc_name = type(exc).__name__
                    # Classify if error is transient (e.g. rate limits, timeouts, temporary server issues)
                    is_transient = any(
                        t_word in exc_name.lower() or t_word in str(exc).lower()
                        for t_word in ["quota", "rate", "429", "timeout", "conn", "503", "500", "overloaded", "servererror"]
                    )
                    if not is_transient:
                        # Non-transient error, raise immediately
                        raise exc
                    
                    last_exc = exc
                    logger.warning(
                        "Transient failure encountered in %s: %s. Attempt %d/%d. Retrying in %.2f seconds...",
                        func.__name__, exc, attempt + 1, max_retries, delay
                    )
                    time.sleep(delay)
                    delay *= backoff_factor
            
            # If all retries exhausted, raise the last exception
            raise last_exc
        return wrapper
    return decorator
