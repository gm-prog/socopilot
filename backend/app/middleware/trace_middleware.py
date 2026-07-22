from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

from app.core.trace import bind_context, clear_context

CORRELATION_HEADER = "x-correlation-id"


class TraceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        correlation_id = request.headers.get(CORRELATION_HEADER) or str(uuid4())

        bind_context(
            correlation_id=correlation_id,
            stage="api",
        )

        response = await call_next(request)

        response.headers[CORRELATION_HEADER] = correlation_id

        clear_context()
        return response
