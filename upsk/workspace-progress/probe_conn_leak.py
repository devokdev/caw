"""Module 4 probe: connection leak on cache error paths (Bug #6 class).

cache.get_redirect_target/set/invalidate acquire an aioredis client and call
aclose() only on the happy path; if any await raises, the client is leaked
until GC. Force the error path by calling with Redis down and count live
connections to Redis after each call via CLIENT LIST.
"""
import asyncio
import logging

from app.services import cache as cache_service

logging.getLogger("linkops").setLevel(logging.CRITICAL)


def redis_client_count():
    import redis

    r = redis.Redis(host="localhost", port=6379, protocol=2)
    n = len(r.client_list())
    r.close()
    return n


async def force_error_path():
    # Point at a dead port so get_redis_client() connects but the op fails.
    import app.config as config

    original = config.settings.redis_url
    config.settings.redis_url = "redis://localhost:6399/0"
    try:
        await cache_service.get_redirect_target("nope")
        await cache_service.set_redirect_target("nope", 1, "https://x")
        await cache_service.invalidate_redirect_target("nope")
    finally:
        config.settings.redis_url = original


def main():
    print(f"redis connections BEFORE error-path calls: {redis_client_count()}")
    for i in range(5):
        asyncio.run(force_error_path())
        import gc

        gc.collect()
        print(f"after round {i + 1}: {redis_client_count()}")
    print("done")


if __name__ == "__main__":
    main()