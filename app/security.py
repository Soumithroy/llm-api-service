"""API-key auth + per-key token-bucket rate limiting."""
import time
from collections import defaultdict
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from app.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str | None = Depends(api_key_header)) -> str:
    if not key or key not in get_settings().api_keys:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or missing X-API-Key")
    return key


@dataclass
class Bucket:
    tokens: float
    updated: float


class TokenBucketLimiter:
    """Classic token bucket: `capacity` requests, refilled continuously over 60s."""

    def __init__(self, per_minute: int):
        self.capacity = per_minute
        self.rate = per_minute / 60.0
        self.buckets: dict[str, Bucket] = defaultdict(lambda: Bucket(self.capacity, time.monotonic()))

    def allow(self, key: str) -> tuple[bool, float]:
        b = self.buckets[key]
        now = time.monotonic()
        b.tokens = min(self.capacity, b.tokens + (now - b.updated) * self.rate)
        b.updated = now
        if b.tokens >= 1:
            b.tokens -= 1
            return True, 0.0
        return False, (1 - b.tokens) / self.rate


limiter = TokenBucketLimiter(get_settings().rate_limit_per_minute)


def rate_limit(request: Request, key: str = Depends(require_api_key)) -> str:
    ok, retry_after = limiter.allow(key)
    if not ok:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Rate limit exceeded",
            headers={"Retry-After": str(int(retry_after) + 1)},
        )
    return key
