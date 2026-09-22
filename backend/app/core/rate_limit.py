"""Shared SlowAPI rate limiter.

Keyed by the original client IP (X-Forwarded-For / X-Real-IP first, falling
back to the direct peer) so limits still work correctly when traffic arrives
through the nginx container, which forwards those headers.

Storage is in-process memory — appropriate for the single API container; switch
to a Redis storage URI (RATELIMIT_STORAGE_URI) before horizontally scaling.
"""

import os

from fastapi import Request
from slowapi import Limiter


def _auth_limit(default: str) -> str:
    """Return the effective limit for an auth endpoint.

    Tests issue many sequential auth calls within one minute; collapse the
    limit while running under pytest so the suite is not throttled.
    """
    if "PYTEST_CURRENT_TEST" in os.environ or os.environ.get("TESTING"):
        return "1000/minute"
    return default


def get_client_key(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=get_client_key)

# Effective limits (see _auth_limit): enforced only outside test runs.
AUTH_LIMITS = {
    "login": lambda: _auth_limit("10/minute"),
    "register": lambda: _auth_limit("5/minute"),
    "refresh": lambda: _auth_limit("60/minute"),
}
