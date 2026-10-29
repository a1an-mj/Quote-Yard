"""Quote Yard API.  Run from the repo root:  uvicorn api.main:app --reload"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.ratelimit import RateLimiter, RateLimitMiddleware
from api.routes import catalog, health, listings, products

API_PREFIX = "/api/v1"
DEFAULT_RATE_LIMIT = 120  # requests per minute, per client address


def cors_origins() -> list[str]:
    raw = os.environ.get("QUOTE_YARD_CORS_ORIGINS", "http://localhost:5173")
    return [o.strip() for o in raw.split(",") if o.strip()]


def rate_limit_per_minute() -> int:
    raw = os.environ.get("QUOTE_YARD_RATE_LIMIT")
    if raw is None or not raw.strip():
        return DEFAULT_RATE_LIMIT
    try:
        value = int(raw)
    except ValueError:
        value = -1
    if value < 0:
        raise RuntimeError(
            "QUOTE_YARD_RATE_LIMIT must be a whole number of requests per "
            f"minute (0 disables it), got {raw!r}"
        )
    return value


def create_app(rate_limit: int | None = None) -> FastAPI:
    app = FastAPI(
        title="Quote Yard API",
        version="0.1.0",
        openapi_url=f"{API_PREFIX}/openapi.json",
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=None,
    )
    limit = rate_limit_per_minute() if rate_limit is None else rate_limit
    if limit > 0:
        app.add_middleware(
            RateLimitMiddleware,
            limiter=RateLimiter(limit),
            exempt_paths=(f"{API_PREFIX}/health",),
        )
    # Added last, so it is outermost: even 429 responses carry CORS headers.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins(),
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix=API_PREFIX)
    app.include_router(catalog.router, prefix=API_PREFIX)
    app.include_router(listings.router, prefix=API_PREFIX)
    app.include_router(products.router, prefix=API_PREFIX)
    return app


app = create_app()
