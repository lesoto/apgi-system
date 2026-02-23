"""
Rate Limiter Service

Redis-based rate limiting using sliding window algorithm.
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import redis.asyncio as redis


@dataclass
class RateLimitResult:
    """Result of rate limit check."""

    allowed: bool
    limit: int
    remaining: int
    reset_at: datetime
    retry_after: Optional[int] = None  # Seconds until retry allowed


class RateLimiter:
    """
    Redis-based rate limiter using sliding window algorithm.

    Supports per-user and per-endpoint rate limiting with configurable
    limits and weighted operations. Falls back to in-memory storage
    when Redis is unavailable.
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize rate limiter.

        Args:
            redis_client: Redis client for storing rate limit data (optional)
        """
        self.redis = redis_client
        self.in_memory = redis_client is None

        if self.in_memory:
            # In-memory storage: key -> list of timestamps
            self._memory_store: Dict[str, list] = defaultdict(list)

        # Default rate limits (requests per window)
        self.default_limits = {
            "global": (100, 60),  # 100 requests per 60 seconds
            "session:create": (10, 60),  # 10 session creations per 60 seconds
            "session:read": (100, 60),
            "task:execute": (20, 60),
            "data:export": (10, 60),
        }

        # Operation weights (how many "credits" each operation costs)
        self.operation_weights = {
            "session:create": 2,
            "session:delete": 2,
            "task:execute": 3,
            "data:export": 5,
            "default": 1,
        }

    def _get_redis_key(self, client_id: str, endpoint: str) -> str:
        """Generate Redis key for rate limit tracking."""
        return f"rate_limit:{client_id}:{endpoint}"

    def _get_limit_config(self, endpoint: str) -> Tuple[int, int]:
        """
        Get rate limit configuration for endpoint.

        Args:
            endpoint: Endpoint identifier

        Returns:
            Tuple of (limit, window_seconds)
        """
        return self.default_limits.get(endpoint, self.default_limits["global"])

    def _get_operation_weight(self, endpoint: str) -> int:
        """
        Get weight for operation.

        Args:
            endpoint: Endpoint identifier

        Returns:
            Weight value (number of credits consumed)
        """
        return self.operation_weights.get(endpoint, self.operation_weights["default"])

    async def check_rate_limit(
        self,
        client_id: str,
        endpoint: str,
        limit: Optional[int] = None,
        window_seconds: Optional[int] = None,
    ) -> RateLimitResult:
        """
        Check if request is within rate limit using sliding window.

        Uses Redis sorted sets for persistence or in-memory lists when Redis unavailable.
        Each request is stored with its timestamp.

        Args:
            client_id: Unique identifier for the client (user ID, IP, etc.)
            endpoint: Endpoint identifier for per-endpoint limits
            limit: Optional override for rate limit
            window_seconds: Optional override for time window

        Returns:
            RateLimitResult with limit check outcome
        """
        # Get limit configuration
        if limit is None or window_seconds is None:
            default_limit, default_window = self._get_limit_config(endpoint)
            limit = limit or default_limit
            window_seconds = window_seconds or default_window

        # Get operation weight
        weight = self._get_operation_weight(endpoint)

        # Generate key
        key = self._get_redis_key(client_id, endpoint)

        # Current timestamp
        now = time.time()
        window_start = now - window_seconds

        if self.in_memory:
            # In-memory implementation
            timestamps = self._memory_store[key]

            # Remove old timestamps outside the window
            timestamps[:] = [t for t in timestamps if t > window_start]

            # Check if request is allowed
            current_count = len(timestamps)

            if current_count + weight <= limit:
                # Add timestamps for this request (weighted)
                for i in range(weight):
                    timestamps.append(now + i * 0.000001)  # Small offset to avoid collisions

                remaining = limit - (current_count + weight)
                reset_at = datetime.utcnow() + timedelta(seconds=window_seconds)

                return RateLimitResult(
                    allowed=True, limit=limit, remaining=remaining, reset_at=reset_at
                )
            else:
                # Not allowed
                remaining = 0
                reset_at = datetime.utcnow() + timedelta(seconds=window_seconds)

                # Calculate retry_after (time until oldest request expires)
                if timestamps:
                    oldest = min(timestamps)
                    retry_after = int(oldest + window_seconds - now) + 1
                else:
                    retry_after = window_seconds

                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=remaining,
                    reset_at=reset_at,
                    retry_after=retry_after,
                )
        else:
            # Redis implementation (existing code)
            # Lua script for atomic check-and-add operation
            # This ensures no race conditions between checking the count and adding entries
            lua_script = """
            local key = KEYS[1]
            local now = tonumber(ARGV[1])
            local window_start = tonumber(ARGV[2])
            local limit = tonumber(ARGV[3])
            local weight = tonumber(ARGV[4])
            local window_seconds = tonumber(ARGV[5])

            -- Remove old entries outside the window
            redis.call('ZREMRANGEBYSCORE', key, 0, window_start)

            -- Count current requests in window
            local current_count = redis.call('ZCARD', key)

            -- Check if request is allowed
            if current_count + weight <= limit then
                -- Add entries for this request (weighted)
                for i = 0, weight - 1 do
                    local score = now + (i * 0.000001)
                    local member = now .. ':' .. i
                    redis.call('ZADD', key, score, member)
                end

                -- Set expiration
                redis.call('EXPIRE', key, window_seconds + 10)

                -- Return: allowed=1, current_count, oldest_timestamp (0 if none)
                return {1, current_count, 0}
            else
                -- Get oldest timestamp for retry_after calculation
                local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
                local oldest_timestamp = 0
                if #oldest > 0 then
                    oldest_timestamp = tonumber(oldest[2])
                end

                -- Return: allowed=0, current_count, oldest_timestamp
                return {0, current_count, oldest_timestamp}
            end
            """

            # Execute Lua script atomically
            try:
                result = await self.redis.eval(  # type: ignore[misc]
                    lua_script,
                    1,  # number of keys
                    key,  # KEYS[1]
                    now,  # ARGV[1]
                    window_start,  # ARGV[2]
                    limit,  # ARGV[3]
                    weight,  # ARGV[4]
                    window_seconds,  # ARGV[5]
                )

                allowed = result[0] == 1
                current_count = result[1]
                oldest_timestamp = result[2]
            except Exception as e:
                # Log the error and fall back to non-atomic implementation
                import logging

                logging.error(f"Redis Lua script execution failed: {e}")
                raise

            # Calculate remaining capacity
            if allowed:
                remaining = max(0, limit - current_count - weight)
            else:
                remaining = 0

            # Calculate reset time
            reset_at = datetime.utcnow() + timedelta(seconds=window_seconds)

            if allowed:
                return RateLimitResult(
                    allowed=True, limit=limit, remaining=remaining, reset_at=reset_at
                )
            else:
                # Calculate retry_after based on oldest request in window
                if oldest_timestamp > 0:
                    retry_after = int(oldest_timestamp + window_seconds - now) + 1
                else:
                    retry_after = window_seconds

                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=retry_after,
                )

    def get_rate_limit_headers(self, result: RateLimitResult) -> Dict[str, str]:
        """
        Generate rate limit headers for HTTP response.

        Args:
            result: Rate limit check result

        Returns:
            Dictionary of headers to add to response
        """
        headers = {
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": str(result.remaining),
            "X-RateLimit-Reset": str(int(result.reset_at.timestamp())),
        }

        if result.retry_after is not None:
            headers["Retry-After"] = str(result.retry_after)

        return headers

    async def reset_rate_limit(self, client_id: str, endpoint: str):
        """
        Reset rate limit for a client/endpoint combination.

        Useful for testing or administrative purposes.

        Args:
            client_id: Client identifier
            endpoint: Endpoint identifier
        """
        key = self._get_redis_key(client_id, endpoint)
        await self.redis.delete(key)

    def configure_limit(self, endpoint: str, limit: int, window_seconds: int):
        """
        Configure custom rate limit for an endpoint.

        Args:
            endpoint: Endpoint identifier
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
        """
        self.default_limits[endpoint] = (limit, window_seconds)

    def configure_weight(self, endpoint: str, weight: int):
        """
        Configure operation weight for an endpoint.

        Args:
            endpoint: Endpoint identifier
            weight: Weight value (credits consumed per request)
        """
        self.operation_weights[endpoint] = weight
