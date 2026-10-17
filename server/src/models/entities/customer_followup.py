#!/usr/bin/env python3
"""客户跟进记录表 ORM 实体。

跟进留痕（铁律：事件/动作可审计）：
    - 客户管理 + 任务调度 Agent 产出的跟进任务写入本表（record_followup）
    - FOLLOWUP_CREATED 协作事件由子图写入 state.events，统一经 AgentTaskService
      落 agent_events 表并发布，本表不自行双写事件
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infras.database import Base


class CustomerFollowup(Base):
    """客户跟进记录（对应 customer_followups 表）。"""

    __tablename__ = "customer_followups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键")
    customer_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False, comment="业务客户编号（与 customers.customer_id 对齐）")
    action: Mapped[str] = mapped_column(String(32), nullable=False, comment="跟进动作（call/visit/message/contract/status_change）")
    content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="跟进内容")
    operator: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="操作人（Agent=customer / 人工=账号）")
    next_followup_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="由此动作约定的下次跟进时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CustomerFollowup id={self.id} cid={self.customer_id} action={self.action}>"
