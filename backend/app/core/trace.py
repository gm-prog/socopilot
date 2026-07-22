from typing import Optional
from contextvars import ContextVar

_correlation_id = ContextVar("correlation_id", default=None)
_stage = ContextVar("stage", default=None)
_raw_event_id = ContextVar("raw_event_id", default=None)
def bind_context(**kwargs):
    if "correlation_id" in kwargs:
        _correlation_id.set(kwargs["correlation_id"])
    if "stage" in kwargs:
        _stage.set(kwargs["stage"])
    if "raw_event_id" in kwargs:
        _raw_event_id.set(kwargs["raw_event_id"])
def clear_context():
    _correlation_id.set(None)
    _stage.set(None)
    _raw_event_id.set(None)
def get_correlation_id():
    return _correlation_id.get()
def get_stage():
    return _stage.get()
def get_raw_event_id():
    return _raw_event_id.get()
try:
    from celery import current_task
except Exception:
    current_task = None
def get_celery_correlation_id() -> Optional[str]:
    try:
        if current_task and hasattr(current_task.request, "headers"):
            return current_task.request.headers.get("correlation_id")
    except Exception:
        return None
    return None
def init_worker_context(stage: str = "worker"):
    correlation_id = get_celery_correlation_id()
    if correlation_id:
        bind_context(
            correlation_id=correlation_id,
            stage=stage,
        )
