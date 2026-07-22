from slowapi import Limiter
from slowapi.util import get_remote_address

# Limit to 100 requests per minute per IP for sensitive endpoints
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
