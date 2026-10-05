import time
import hashlib
from collections import OrderedDict
from uuid import uuid4
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.services.cache import cache
from app.core.logging import log_event
from app.config import get_settings


class RequestMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.buckets = OrderedDict()

    async def dispatch(self, request, call_next):
        request_id = str(uuid4())
        request.state.request_id = request_id
        started = time.monotonic()
        client = request.client.host if request.client else "unknown"
        auth = "/auth/" in request.url.path
        limit = 20 if auth else 300
        window = int(time.time() // 60)
        key = f"rate:{hashlib.sha256(client.encode()).hexdigest()[:20]}:{'auth' if auth else 'api'}:{window}"
        try:
            if cache.redis:
                count = await cache.redis.eval(
                    "local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],ARGV[1]); end; return n",
                    1,
                    key,
                    120,
                )
            else:
                count = self.buckets.get(key, 0) + 1
                self.buckets[key] = count
                while len(self.buckets) > 10000:
                    self.buckets.popitem(last=False)
            if count > limit:
                response = JSONResponse(
                    {
                        "success": False,
                        "error": {"code": "RATE_LIMITED", "message": "Too many requests. Retry shortly."},
                    },
                    429,
                    headers={"Retry-After": "60"},
                )
            elif (request.url.path.rstrip("/") != get_settings().api_v1_prefix + "/predict/image"
                  and int(request.headers.get("content-length", "0")) > 7_000_000):
                response = JSONResponse(
                    {"success": False, "error": {"code": "REQUEST_TOO_LARGE", "message": "Request body exceeds 7 MB."}},
                    413,
                )
            else:
                response = await call_next(request)
        except Exception as exc:
            log_event("request_failed", request_id=request_id, error_type=type(exc).__name__)
            response = JSONResponse(
                {
                    "success": False,
                    "error": {"code": "INTERNAL_ERROR", "message": "The request could not be completed."},
                },
                500,
            )
        response.headers.update(
            {
                "X-Request-ID": request_id,
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Referrer-Policy": "no-referrer",
                "Cache-Control": "no-store",
            }
        )
        route = request.scope.get("route")
        path = getattr(route, "path", "unmatched")
        log_event(
            "request",
            request_id=request_id,
            endpoint=path,
            method=request.method,
            status=response.status_code,
            duration_ms=round((time.monotonic() - started) * 1000, 2),
        )
        return response
