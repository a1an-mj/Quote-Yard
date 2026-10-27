import os

# The API tests share one app instance; keep the rate limiter out of their way.
# tests/test_api_ratelimit.py builds its own apps with explicit limits.
os.environ["QUOTE_YARD_RATE_LIMIT"] = "0"
