"""PII redaction middleware for request/response logging paths."""

import re
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)

# Patterns for common PII — applied to log context only in Phase 0
PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[REDACTED_IP]"),
    (re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[REDACTED_PHONE]"),
]


def redact_pii(text: str) -> str:
    """Redact known PII patterns from a string."""
    result = text
    for pattern, replacement in PII_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


class PIIRedactionMiddleware(BaseHTTPMiddleware):
    """Attach redacted path info to logs; full body redaction in later phases."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        safe_path = redact_pii(str(request.url.path))
        logger.info(
            "http_request",
            method=request.method,
            path=safe_path,
            client=request.client.host if request.client else None,
        )
        response = await call_next(request)
        return response
