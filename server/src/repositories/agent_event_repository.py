#!/usr/bin/env python3
"""Agent 协作事件仓储（数据访问层，无业务逻辑）。"""

from __future__ import annotations

from sqlalchemy import desc

from src.models.entities.agent_event import AgentEvent
from src.repositories.base_repository import BaseRepository


class AgentEventRepository(BaseRepository[AgentEvent]):
    """AgentEvent 表数据访问。"""

    model_class = AgentEvent

    def list_by_type(self, event_type: str, offset: int = 0, limit: int = 20) -> list[AgentEvent]:
        """按事件类型分页查询。"""
        return self.list(
            AgentEvent.event_type == event_type,
            order_by=desc(AgentEvent.id),
            offset=offset,
            limit=limit,
        )

    def list_recent(self, offset: int = 0, limit: int = 20) -> list[AgentEvent]:
        """最近事件（管理后台事件面板）。"""
        return self.list(order_by=desc(AgentEvent.id), offset=offset, limit=limit)
