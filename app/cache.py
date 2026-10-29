"""Tiny TTL cache: identical prompts don't pay for a second LLM call."""
import hashlib
import time


class TTLCache:
    def __init__(self, ttl: int, max_items: int = 1000):
        self.ttl, self.max_items = ttl, max_items
        self._data: dict[str, tuple[float, object]] = {}

    @staticmethod
    def key(*parts: str) -> str:
        return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()

    def get(self, k: str):
        hit = self._data.get(k)
        if not hit:
            return None
        expires, value = hit
        if time.monotonic() > expires:
            self._data.pop(k, None)
            return None
        return value

    def set(self, k: str, value) -> None:
        if len(self._data) >= self.max_items:
            self._data.pop(next(iter(self._data)))  # evict oldest
        self._data[k] = (time.monotonic() + self.ttl, value)
