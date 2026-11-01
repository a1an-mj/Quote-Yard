"""Per-client sliding-window rate limiting (in-process, no dependencies)."""

import math
import threading
import time
from collections import deque

from starlette.responses import JSONResponse


class RateLimiter:
    """Allow `limit` requests per `window` seconds for each client key."""

    def __init__(self, limit, window=60.0, max_clients=10_000, clock=time.monotonic):
        if limit < 1:
            raise ValueError("limit must be at least 1")
        self.limit = limit
        self.window = window
        self.max_clients = max_clients
        self.clock = clock
        self.hits: dict[str, deque] = {}
        self._lock = threading.Lock()

    def check(self, key):
        """Return None if the request is allowed, else seconds until it would be."""
        now = self.clock()
        cutoff = now - self.window
        with self._lock:
            hits = self.hits.get(key)
            if hits is None:
                if len(self.hits) >= self.max_clients:
                    self._make_room(cutoff)
                hits = self.hits[key] = deque()
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= self.limit:
                return max(hits[0] + self.window - now, 0.0)
            hits.append(now)
            return None

    def _make_room(self, cutoff):
        """Drop clients with no recent hits; if still full, drop the oldest one."""
        expired = [k for k, h in self.hits.items() if not h or h[-1] <= cutoff]
        for key in expired:
            del self.hits[key]
        if len(self.hits) >= self.max_clients:
            del self.hits[next(iter(self.hits))]


class RateLimitMiddleware:
    """Pure ASGI middleware. Counts by the client address in the ASGI scope.

    Only paths under `prefix` count, so loading the site's files does not use
    up a visitor's API allowance.
    """

    def __init__(self, app, limiter, exempt_paths=(), prefix=""):
        self.app = app
        self.limiter = limiter
        self.exempt_paths = frozenset(exempt_paths)
        self.prefix = prefix

    async def __call__(self, scope, receive, send):
        if (
            scope["type"] != "http"
            or scope["path"] in self.exempt_paths
            or not scope["path"].startswith(self.prefix)
        ):
            await self.app(scope, receive, send)
            return
        client = scope.get("client")
        wait = self.limiter.check(client[0] if client else "unknown")
        if wait is None:
            await self.app(scope, receive, send)
            return
        response = JSONResponse(
            {"detail": "rate limit exceeded"},
            status_code=429,
            headers={"Retry-After": str(max(1, math.ceil(wait)))},
        )
        await response(scope, receive, send)
