# Module 06: Graceful Degradation & Circuit Breakers

## Resilience Implementation Architecture

### 1. Explicit Timeouts on External Dependencies
- **Database (`asyncpg`/`SQLAlchemy`)**: Client-side query timeout wrapped at `1.0s` with server backstop `statement_timeout = 2000ms`.
- **Redis (`aioredis`/`redis-py`)**: Socket timeout configured to `0.5s` for cache and rate-limiting lookups.

### 2. Circuit Breaker (`pybreaker` implementation)
```python
import pybreaker
import logging

logger = logging.getLogger("resilience")

db_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    name="postgres_breaker"
)

redis_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=15,
    name="redis_cache_breaker"
)
```

### 3. Exponential Backoff with Jitter for Transient Retries
```python
import asyncio
import random

async def retry_with_jitter(coro_fn, max_retries=3, base_delay=0.1, max_delay=2.0, jitter=0.05):
    for attempt in range(max_retries + 1):
        try:
            return await coro_fn()
        except (ConnectionError, asyncio.TimeoutError) as e:
            if attempt == max_retries:
                raise
            delay = min(base_delay * (2 ** attempt), max_delay) + random.uniform(-jitter, jitter)
            await asyncio.sleep(max(0, delay))
```
