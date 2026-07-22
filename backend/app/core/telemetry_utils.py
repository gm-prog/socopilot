import time
from functools import wraps
from app.core.metrics import INGEST_LATENCY, PROVIDER_FAILURES

def track_latency(histogram):
    """Decorator to measure execution time of a function."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                histogram.labels(stage="success").observe(time.time() - start_time)
                return result
            except Exception as e:
                histogram.labels(stage="error").observe(time.time() - start_time)
                raise e
        return wrapper
    return decorator
