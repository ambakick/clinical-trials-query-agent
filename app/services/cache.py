from __future__ import annotations

import asyncio
import time
from typing import Any

import orjson


def stable_dumps(payload: Any) -> str:
    return orjson.dumps(payload, option=orjson.OPT_SORT_KEYS).decode("utf-8")


def build_cache_key(namespace: str, version: str, payload: Any) -> str:
    return f"{namespace}:{version}:{stable_dumps(payload)}"


class CacheBackend:
    async def get(self, key: str) -> Any | None:
        raise NotImplementedError

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        raise NotImplementedError


class InMemoryCacheBackend(CacheBackend):
    def __init__(self) -> None:
        self._data: dict[str, tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            record = self._data.get(key)
            if record is None:
                return None
            expires_at, value = record
            if expires_at < time.monotonic():
                self._data.pop(key, None)
                return None
            return value

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        async with self._lock:
            self._data[key] = (time.monotonic() + ttl_seconds, value)

