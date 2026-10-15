#!/usr/bin/env python3
"""缓存基础设施（北辰 x-BeiChen）。

统一缓存抽象：
    - InMemoryCacheProvider：骨架默认（进程内 dict + TTL），零依赖
    - RedisCacheProvider：生产实现（redis 客户端封装，需 RedisConfig.enabled）

用途：Agent 任务幂等去重、检查点缓存、配置热载、RAG 结果缓存等。
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any

from src.core.config import settings
from src.core.logger import logger


class CacheProvider(ABC):
    """缓存抽象接口。"""

    @abstractmethod
    def get(self, key: str) -> Any | None: ...

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...


class InMemoryCacheProvider(CacheProvider):
    """进程内缓存（骨架默认）。"""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float | None]] = {}

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if item is None:
            return None
        value, expire_at = item
        if expire_at is not None and time.time() > expire_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        expire_at = time.time() + ttl_seconds if ttl_seconds else None
        self._store[key] = (value, expire_at)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)


class RedisCacheProvider(CacheProvider):
    """Redis 缓存实现（生产预留）。需 RedisConfig.enabled。"""

    def __init__(self) -> None:
        import redis

        self._client = redis.Redis.from_url(settings.redis.url, decode_responses=True)

    def get(self, key: str) -> Any | None:
        return self._client.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        self._client.set(key, value, ex=ttl_seconds)

    def delete(self, key: str) -> None:
        self._client.delete(key)


@lru_cache(maxsize=1)
def get_cache_provider() -> CacheProvider:
    """缓存工厂（单例）。"""
    provider: CacheProvider
    if settings.redis.enabled:
        provider = RedisCacheProvider()
        logger.info("Cache 初始化：RedisCacheProvider")
    else:
        provider = InMemoryCacheProvider()
        logger.info("Cache 初始化：InMemoryCacheProvider（骨架）")
    return provider


__all__ = ["CacheProvider", "InMemoryCacheProvider", "RedisCacheProvider", "get_cache_provider"]
