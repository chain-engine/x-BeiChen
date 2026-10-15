#!/usr/bin/env python3
"""事件总线基础设施（北辰 x-BeiChen）。

Agent 之间、Agent 与业务侧之间的协作事件传递通道。
    - EventMessage：传输对象（事件类型 / 来源 / 目标 / 载荷）
    - InMemoryEventBus：骨架默认（进程内队列 + 订阅者回调），零依赖
    - RedisStreamEventBus：生产预留（Redis Stream 持久化 + 消费组，需 RedisConfig.enabled）

订阅模型：消费者以「事件类型 + 目标 Agent」订阅，事件总线负责投递。
生产环境建议：发布侧写 Redis Stream（带 TTL），消费侧用消费组横向扩容。
"""

from __future__ import annotations

import asyncio
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Callable

from src.core.config import settings
from src.core.logger import logger
from src.constants import EventType


@dataclass
class EventMessage:
    """事件总线传输对象。"""

    event_type: EventType
    payload: dict[str, Any] = field(default_factory=dict)
    source_agent: str | None = None
    target_agent: str | None = None
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC).isoformat())

    @classmethod
    def of(cls, event_type: EventType, payload: dict[str, Any], source: str | None = None, target: str | None = None) -> "EventMessage":
        return cls(event_type=event_type, payload=payload, source_agent=source, target_agent=target)


class EventBus(ABC):
    """事件总线抽象接口。"""

    @abstractmethod
    async def publish(self, message: EventMessage) -> None:
        """发布事件。"""

    @abstractmethod
    async def subscribe(self, event_type: EventType, handler: Callable[[EventMessage], Any]) -> None:
        """订阅某类事件（订阅者回调）。"""


class InMemoryEventBus(EventBus):
    """进程内事件总线（骨架默认）。单机可用，重启丢事件；生产替换为 Redis 实现。"""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[EventMessage], Any]]] = {}

    async def publish(self, message: EventMessage) -> None:
        logger.info(f"[EventBus] publish: {message.event_type} -> {message.target_agent or '*'} (id={message.event_id})")
        for handler in self._handlers.get(str(message.event_type), []):
            try:
                result = handler(message)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as exc:
                logger.exception(f"[EventBus] handler 异常: {exc}")

    async def subscribe(self, event_type: EventType, handler: Callable[[EventMessage], Any]) -> None:
        key = str(event_type)
        self._handlers.setdefault(key, []).append(handler)
        logger.info(f"[EventBus] subscribe: {event_type}")


class RedisStreamEventBus(EventBus):
    """Redis Stream 事件总线（生产预留）。
    发布：XADD 写入 Stream（带 TTL 过期）；订阅：XREADGROUP 消费组横向扩容。
    依赖 redis 客户端，RedisConfig.enabled 为 True 时由工厂创建。
    """

    def __init__(self, stream_key: str | None = None, group: str = "beichen-events") -> None:
        import redis.asyncio as redis

        self._stream_key = stream_key or settings.agent.event_bus_stream
        self._group = group
        self._client = redis.from_url(settings.redis.url)

    async def publish(self, message: EventMessage) -> None:
        # TODO(二期): XADD + 消费组；骨架阶段仅记录日志
        logger.info(f"[EventBus-Redis] 预留实现，未接入。event={message.event_type}")

    async def subscribe(self, event_type: EventType, handler: Callable[[EventMessage], Any]) -> None:
        # TODO(二期): XREADGROUP 后台任务消费
        logger.warning("[EventBus-Redis] subscribe 为预留实现，当前未消费事件")


_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """事件总线工厂（单例）：按配置选择内存 / Redis 实现。"""
    global _event_bus
    if _event_bus is None:
        if settings.redis.enabled:
            _event_bus = RedisStreamEventBus()
        else:
            _event_bus = InMemoryEventBus()
        logger.info(f"EventBus 初始化：{type(_event_bus).__name__}")
    return _event_bus


__all__ = ["EventMessage", "EventBus", "InMemoryEventBus", "RedisStreamEventBus", "get_event_bus"]
