#!/usr/bin/env python3
"""Agent 协作事件表 ORM 实体。

事件（审批通过、任务失败等）持久化落库，
供管理后台事件面板查询与事后审计（对齐"资金操作必须留痕"的要求）。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infras.database import Base


class AgentEvent(Base):
    """Agent 协作事件实体（对应 agent_events 表）。"""

    __tablename__ = "agent_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键")
    event_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="事件类型（EventType）")
    source_agent: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="来源 Agent")
    target_agent: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="目标 Agent / 消费者")
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="事件载荷")
    status: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="消费状态（预留）")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AgentEvent id={self.id} type={self.event_type} source={self.source_agent}>"
