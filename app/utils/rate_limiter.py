from __future__ import annotations

import asyncio
import time
from collections import deque


class AsyncSlidingWindowRateLimiter:
    def __init__(self, max_requests: int, period_seconds: float = 60.0) -> None:
        self.max_requests = max_requests
        self.period_seconds = period_seconds
        self._events: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                now = time.monotonic()
                while self._events and now - self._events[0] >= self.period_seconds:
                    self._events.popleft()
                if len(self._events) < self.max_requests:
                    self._events.append(now)
                    return
                wait_seconds = self.period_seconds - (now - self._events[0])
            await asyncio.sleep(max(wait_seconds, 0.01))

