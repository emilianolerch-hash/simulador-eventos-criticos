"""Rate limiting in-memory por IP. Ventana deslizante de 60 segundos."""
import time
from collections import defaultdict, deque
from typing import Callable

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self._max = max_requests
        self._window = window_seconds
        self._log: dict[str, deque] = defaultdict(deque)

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def clear(self) -> None:
        """Reset all counters — only for testing."""
        self._log.clear()

    def __call__(self, request: Request) -> None:
        ip = self._client_ip(request)
        now = time.monotonic()
        window_start = now - self._window
        q = self._log[ip]

        # Drop timestamps outside the window
        while q and q[0] < window_start:
            q.popleft()

        if len(q) >= self._max:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Demasiados intentos. Esperá {self._window} segundos.",
                headers={"Retry-After": str(self._window)},
            )

        q.append(now)


def make_limiter(max_requests: int, window_seconds: int = 60) -> Callable:
    """Returns a FastAPI dependency that applies rate limiting."""
    limiter = RateLimiter(max_requests, window_seconds)
    return limiter
