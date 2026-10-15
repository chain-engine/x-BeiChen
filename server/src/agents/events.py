#!/usr/bin/env python3
"""Agent 事件构造 helper（收口事件 dict 的字段结构）。

节点不再手拼 {"type":..., "source":..., "payload":...}，统一走 build_event，
避免字段名拼错、source 漏填、payload 类型不一致。
"""

from __future__ import annotations

from typing import Any

from src.constants import EventType


def build_event(
    event_type: EventType,
    source: str,
    payload: dict[str, Any] | None = None,
    target: str | None = None,
) -> dict[str, Any]:
    """构造一条协作事件（与 agent_events 表字段对齐）。"""
    return {
        "type": event_type,
        "source": source,
        "target": target,
        "payload": payload or {},
    }
