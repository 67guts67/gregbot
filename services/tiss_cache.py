# services/cache.py
import time
import asyncio
from functools import wraps

class TTLCache:
    def __init__(self):
        self._store: dict[tuple, tuple[float, object]] = {}
        self._locks: dict[tuple, asyncio.Lock] = {}
        self._sweep_task: asyncio.Task | None = None

    def cached(self, ttl: int, miss_ttl: int | None = None):

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                key = (func.__name__, args, tuple(sorted(kwargs.items())))
                lock = self._locks.setdefault(key, asyncio.Lock())

                now = time.monotonic()
                cached = self._store.get(key)
                if cached and cached[0] > now:
                    print(f"Cache hit (post-lock): {key}", flush=True)

                    return cached[1]

                async with lock:
                    cached = self._store.get(key)
                    if cached and cached[0] > now:
                        print(f"Cache hit (post-lock): {key}", flush=True)
                        return cached[1]

                    print(f"Cache miss: {key}", flush=True)
                    result = await func(*args, **kwargs)
                    is_empty = result is None or result == []
                    expiry = now + (miss_ttl if is_empty and miss_ttl else ttl)
                    self._store[key] = (expiry, result)
                    return result
            return wrapper

        return decorator

    def start_sweeper(self, interval: int = 60 * 30):
        if self._sweep_task is None:
            self._sweep_task = asyncio.create_task(self._sweep_loop(interval))

    async def _sweep_loop(self, interval: int):
        while True:
            await asyncio.sleep(interval)
            self._sweep()

    def _sweep(self):
        now = time.monotonic()

        expired_keys = [k for k, (expiry, _) in self._store.items() if expiry <= now]
        for k in expired_keys:
            del self._store[k]

        stale_lock_keys = [
            k for k, lock in self._locks.items()
            if not lock.locked() and k not in self._store
        ]
        for k in stale_lock_keys:
            del self._locks[k]

        print(f"Cache sweep: removed {len(expired_keys)} entries, {len(stale_lock_keys)} locks", flush=True)

    def clear(self):
        self._store.clear()
        self._locks.clear()

tiss_cache = TTLCache()