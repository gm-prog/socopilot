from app.core.metrics import ENRICHMENT_LATENCY, PROVIDER_FAILURES
import time

def instrumented_enrichment(provider_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                res = func(*args, **kwargs)
                ENRICHMENT_LATENCY.labels(provider=provider_name).observe(time.time() - start)
                return res
            except Exception as e:
                PROVIDER_FAILURES.labels(provider=provider_name).inc()
                raise e
        return wrapper
    return decorator
