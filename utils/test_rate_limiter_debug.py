"""Debug script to test rate limiter"""

import asyncio

import redis.asyncio as redis

from api.config import settings
from api.services.rate_limiter import RateLimiter


async def test_rate_limiter() -> None:
    # Create Redis client
    redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)  # type: ignore[no-untyped-call]

    try:
        # Create rate limiter
        rate_limiter = RateLimiter(redis_client)

        # Test with simple case: limit=10, weight=2
        client_id = "test_debug_client"
        endpoint = "session:create"

        # Reset
        await rate_limiter.reset_rate_limit(client_id, endpoint)

        # Make requests
        for i in range(10):
            result = await rate_limiter.check_rate_limit(client_id, endpoint)
            key = rate_limiter._get_redis_key(client_id, endpoint)
            count = await redis_client.zcard(key)
            print(
                f"Request {i + 1}: allowed={result.allowed}, remaining={result.remaining}, redis_count={count}"
            )

            if not result.allowed:
                print(f"  -> Denied at request {i + 1}")
                break

    finally:
        await redis_client.close()


if __name__ == "__main__":
    asyncio.run(test_rate_limiter())
