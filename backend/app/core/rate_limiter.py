import time
import threading
from collections import defaultdict, deque
from typing import Dict, Deque, Optional, Callable
from fastapi import Request, HTTPException, status
from app.core.config import settings
from app.core.logging_config import logger

class InMemoryRateLimiter:
    """
    Thread-safe in-memory sliding window rate limiter.
    Does not require external infrastructure like Redis for local/monolithic deployment,
    while maintaining precise request counting within rolling time windows.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._requests: Dict[str, Deque[float]] = defaultdict(deque)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int = 60) -> tuple[bool, int, int]:
        """
        Evaluates whether a request identified by `key` is allowed.
        Returns: (allowed: bool, remaining_requests: int, retry_after_seconds: int)
        """
        if not settings.RATE_LIMIT_ENABLED:
            return True, max_requests, 0

        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            timestamps = self._requests[key]
            
            # Prune timestamps outside the current window
            while timestamps and timestamps[0] < window_start:
                timestamps.popleft()

            current_count = len(timestamps)
            if current_count < max_requests:
                timestamps.append(now)
                remaining = max_requests - current_count - 1
                return True, remaining, 0
            else:
                oldest = timestamps[0]
                retry_after = max(1, int(oldest + window_seconds - now))
                return False, 0, retry_after

    def reset(self, key: Optional[str] = None):
        """Clears rate limit state (useful in testing)."""
        with self._lock:
            if key:
                self._requests.pop(key, None)
            else:
                self._requests.clear()

# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()

def rate_limit(
    max_requests: int,
    window_seconds: int = 60,
    key_prefix: str = "general",
    use_user_id: bool = True
) -> Callable:
    """
    FastAPI dependency factory for applying rate limits to endpoints.
    """
    async def dependency(request: Request):
        if not settings.RATE_LIMIT_ENABLED:
            return

        # Derive identifier from client IP or user authentication
        client_ip = request.client.host if request.client else "127.0.0.1"
        identifier = f"{key_prefix}:{client_ip}"
        
        # Check rate limit
        allowed, remaining, retry_after = rate_limiter.is_allowed(
            key=identifier,
            max_requests=max_requests,
            window_seconds=window_seconds
        )

        if not allowed:
            req_id = getattr(request.state, "request_id", "req-unknown")
            logger.warning(f"[{req_id}] Rate limit exceeded for {identifier} (Limit: {max_requests}/{window_seconds}s)")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Rate limit exceeded for this endpoint. Please retry after {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )

    return dependency
