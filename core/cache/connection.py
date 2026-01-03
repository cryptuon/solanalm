"""
Redis Connection Management for SolanaLM

Provides async Redis client with connection pooling.
"""

import json
import logging
from typing import Optional, Any, List
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from core.config.settings import get_settings

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Async Redis client wrapper with common operations.

    Usage:
        cache = RedisCache()
        await cache.initialize()

        await cache.set("key", "value", ttl=300)
        value = await cache.get("key")

        await cache.close()
    """

    _instance: Optional["RedisCache"] = None

    def __init__(self, redis_url: Optional[str] = None):
        settings = get_settings()
        self.redis_url = redis_url or settings.redis_url

        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[redis.Redis] = None
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "RedisCache":
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def initialize(self) -> None:
        """Initialize Redis connection pool"""
        if self._initialized:
            logger.debug("Redis already initialized")
            return

        try:
            self.pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=50,
                decode_responses=True
            )
            self.client = redis.Redis(connection_pool=self.pool)

            # Test connection
            await self.client.ping()
            self._initialized = True
            logger.info(f"Redis connected: {self.redis_url}")

        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching will be disabled.")
            self._initialized = False

    async def close(self) -> None:
        """Close Redis connections"""
        if self.client:
            await self.client.close()
        if self.pool:
            await self.pool.disconnect()
        self._initialized = False
        logger.info("Redis connections closed")

    @property
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        return self._initialized and self.client is not None

    async def get(self, key: str) -> Optional[str]:
        """Get string value from cache"""
        if not self.is_connected:
            return None
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None
    ) -> bool:
        """Set string value in cache"""
        if not self.is_connected:
            return False
        try:
            if ttl:
                await self.client.setex(key, ttl, value)
            else:
                await self.client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.is_connected:
            return False
        try:
            return await self.client.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.is_connected:
            return False
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False

    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value from cache"""
        data = await self.get(key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return None
        return None

    async def set_json(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set JSON value in cache"""
        try:
            return await self.set(key, json.dumps(value, default=str), ttl)
        except (TypeError, ValueError) as e:
            logger.error(f"JSON serialization error: {e}")
            return False

    async def get_many(self, keys: List[str]) -> List[Optional[str]]:
        """Get multiple values at once"""
        if not self.is_connected or not keys:
            return [None] * len(keys)
        try:
            return await self.client.mget(keys)
        except Exception as e:
            logger.error(f"Redis MGET error: {e}")
            return [None] * len(keys)

    async def set_many(
        self,
        mapping: dict,
        ttl: Optional[int] = None
    ) -> bool:
        """Set multiple values at once"""
        if not self.is_connected or not mapping:
            return False
        try:
            pipe = self.client.pipeline()
            for key, value in mapping.items():
                if ttl:
                    pipe.setex(key, ttl, value)
                else:
                    pipe.set(key, value)
            await pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Redis pipeline error: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter"""
        if not self.is_connected:
            return None
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR error: {e}")
            return None

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on key"""
        if not self.is_connected:
            return False
        try:
            return await self.client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Redis EXPIRE error: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """Get TTL of key (-1 if no expiry, -2 if not exists)"""
        if not self.is_connected:
            return -2
        try:
            return await self.client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error: {e}")
            return -2

    # Set operations (for tracking online nodes, etc.)
    async def sadd(self, key: str, *members: str) -> int:
        """Add members to set"""
        if not self.is_connected:
            return 0
        try:
            return await self.client.sadd(key, *members)
        except Exception as e:
            logger.error(f"Redis SADD error: {e}")
            return 0

    async def srem(self, key: str, *members: str) -> int:
        """Remove members from set"""
        if not self.is_connected:
            return 0
        try:
            return await self.client.srem(key, *members)
        except Exception as e:
            logger.error(f"Redis SREM error: {e}")
            return 0

    async def smembers(self, key: str) -> set:
        """Get all members of set"""
        if not self.is_connected:
            return set()
        try:
            return await self.client.smembers(key)
        except Exception as e:
            logger.error(f"Redis SMEMBERS error: {e}")
            return set()

    async def sismember(self, key: str, member: str) -> bool:
        """Check if member is in set"""
        if not self.is_connected:
            return False
        try:
            return await self.client.sismember(key, member)
        except Exception as e:
            logger.error(f"Redis SISMEMBER error: {e}")
            return False

    # Sorted set operations (for rate limiting)
    async def zadd(
        self,
        key: str,
        mapping: dict,
        nx: bool = False
    ) -> int:
        """Add to sorted set"""
        if not self.is_connected:
            return 0
        try:
            return await self.client.zadd(key, mapping, nx=nx)
        except Exception as e:
            logger.error(f"Redis ZADD error: {e}")
            return 0

    async def zcount(self, key: str, min_score: float, max_score: float) -> int:
        """Count members in score range"""
        if not self.is_connected:
            return 0
        try:
            return await self.client.zcount(key, min_score, max_score)
        except Exception as e:
            logger.error(f"Redis ZCOUNT error: {e}")
            return 0

    async def zremrangebyscore(
        self,
        key: str,
        min_score: float,
        max_score: float
    ) -> int:
        """Remove members in score range"""
        if not self.is_connected:
            return 0
        try:
            return await self.client.zremrangebyscore(key, min_score, max_score)
        except Exception as e:
            logger.error(f"Redis ZREMRANGEBYSCORE error: {e}")
            return 0

    # Distributed locks
    @asynccontextmanager
    async def lock(
        self,
        key: str,
        ttl: int = 30,
        blocking: bool = True,
        timeout: float = 10.0
    ):
        """
        Distributed lock context manager.

        Usage:
            async with cache.lock("my_lock"):
                # Critical section
                pass
        """
        if not self.is_connected:
            yield  # No-op if Redis unavailable
            return

        lock = self.client.lock(key, timeout=ttl, blocking=blocking, blocking_timeout=timeout)
        try:
            acquired = await lock.acquire()
            if not acquired:
                raise TimeoutError(f"Could not acquire lock: {key}")
            yield
        finally:
            try:
                await lock.release()
            except Exception:
                pass  # Lock may have expired

    async def health_check(self) -> bool:
        """Check Redis connectivity"""
        if not self.is_connected:
            return False
        try:
            await self.client.ping()
            return True
        except Exception:
            return False


# Global Redis instance
_redis_cache: Optional[RedisCache] = None


async def init_redis(redis_url: Optional[str] = None) -> RedisCache:
    """Initialize global Redis cache"""
    global _redis_cache
    _redis_cache = RedisCache.get_instance()
    if redis_url:
        _redis_cache.redis_url = redis_url
    await _redis_cache.initialize()
    return _redis_cache


async def close_redis() -> None:
    """Close global Redis cache"""
    global _redis_cache
    if _redis_cache:
        await _redis_cache.close()
        _redis_cache = None


def get_redis() -> Optional[RedisCache]:
    """Get global Redis cache instance"""
    return _redis_cache
