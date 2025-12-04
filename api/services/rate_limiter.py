"""
Rate Limiter Service

Redis-based rate limiting using sliding window algorithm.
"""

import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
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
    limits and weighted operations.
    """
    
    def __init__(self, redis_client: redis.Redis):
        """
        Initialize rate limiter.
        
        Args:
            redis_client: Redis client for storing rate limit data
        """
        self.redis = redis_client
        
        # Default rate limits (requests per window)
        self.default_limits = {
            'global': (100, 60),  # 100 requests per 60 seconds
            'session:create': (10, 60),  # 10 session creations per 60 seconds
            'session:read': (100, 60),
            'task:execute': (20, 60),
            'data:export': (10, 60),
        }
        
        # Operation weights (how many "credits" each operation costs)
        self.operation_weights = {
            'session:create': 2,
            'session:delete': 2,
            'task:execute': 3,
            'data:export': 5,
            'default': 1,
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
        return self.default_limits.get(endpoint, self.default_limits['global'])
    
    def _get_operation_weight(self, endpoint: str) -> int:
        """
        Get weight for operation.
        
        Args:
            endpoint: Endpoint identifier
            
        Returns:
            Weight value (number of credits consumed)
        """
        return self.operation_weights.get(endpoint, self.operation_weights['default'])
    
    async def check_rate_limit(
        self,
        client_id: str,
        endpoint: str,
        limit: Optional[int] = None,
        window_seconds: Optional[int] = None
    ) -> RateLimitResult:
        """
        Check if request is within rate limit using sliding window.
        
        Uses Redis sorted sets to track requests within a time window.
        Each request is stored with its timestamp as the score.
        
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
        
        # Generate Redis key
        key = self._get_redis_key(client_id, endpoint)
        
        # Current timestamp
        now = time.time()
        window_start = now - window_seconds
        
        # Use Redis pipeline for atomic operations
        pipe = self.redis.pipeline()
        
        # Remove old entries outside the window
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count current requests in window
        pipe.zcard(key)
        
        # Execute pipeline
        results = await pipe.execute()
        current_count = results[1]
        
        # Calculate remaining capacity (accounting for weight)
        remaining = max(0, limit - current_count - weight)
        allowed = current_count + weight <= limit
        
        # Calculate reset time
        reset_at = datetime.utcnow() + timedelta(seconds=window_seconds)
        
        if allowed:
            # Add current request to the window with weight
            # We add multiple entries for weighted operations
            pipe = self.redis.pipeline()
            for i in range(weight):
                # Use microsecond precision to avoid collisions
                score = now + (i * 0.000001)
                pipe.zadd(key, {f"{now}:{i}": score})
            
            # Set expiration on the key
            pipe.expire(key, window_seconds + 10)  # Add buffer
            
            await pipe.execute()
            
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=remaining,
                reset_at=reset_at
            )
        else:
            # Calculate retry_after based on oldest request in window
            oldest_scores = await self.redis.zrange(key, 0, 0, withscores=True)
            
            if oldest_scores:
                oldest_timestamp = oldest_scores[0][1]
                retry_after = int(oldest_timestamp + window_seconds - now) + 1
            else:
                retry_after = window_seconds
            
            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_at=reset_at,
                retry_after=retry_after
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
            'X-RateLimit-Limit': str(result.limit),
            'X-RateLimit-Remaining': str(result.remaining),
            'X-RateLimit-Reset': str(int(result.reset_at.timestamp())),
        }
        
        if result.retry_after is not None:
            headers['Retry-After'] = str(result.retry_after)
        
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