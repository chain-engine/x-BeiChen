#!/usr/bin/env python3
"""Agent 任务仓储（数据访问层，无业务逻辑）。"""

from __future__ import annotations

from sqlalchemy import desc, select

from src.models.entities.agent_task import AgentTask
from src.repositories.base_repository import BaseRepository


class AgentTaskRepository(BaseRepository[AgentTask]):
    """AgentTask 表数据访问。

    只提供查询条件组合，状态机流转规则由 services 层控制。
    """

    model_class = AgentTask

    # ----------------------------------------------------------
    # 编排常用查询
    # ----------------------------------------------------------

    def get_by_thread_id(self, thread_id: str) -> AgentTask | None:
        """按 LangGraph 线程 ID 查询任务（断点续跑时定位）。"""
        return self.first(AgentTask.thread_id == thread_id)

    def list_by_status(self, status: str, offset: int = 0, limit: int = 20) -> list[AgentTask]:
        """按状态分页查询。"""
        return self.list(
            AgentTask.status == status,
            order_by=desc(AgentTask.id),
            offset=offset,
            limit=limit,
        )

    def list_by_task_type(self, task_type: str, offset: int = 0, limit: int = 20) -> list[AgentTask]:
        """按任务类型分页查询（如只看监控任务）。"""
        return self.list(
            AgentTask.task_type == task_type,
            order_by=desc(AgentTask.id),
            offset=offset,
            limit=limit,
        )

    def list_overdue_running(self) -> list[AgentTask]:
        """查询超过 timeout_at 仍处于 running/assigned 的任务（用于超时巡检）。"""
        from datetime import UTC, datetime

        return self.list(
            AgentTask.status.in_(["running", "assigned"]),
            AgentTask.timeout_at.is_not(None),
            AgentTask.timeout_at < datetime.now(UTC),
            limit=100,
        )

    def count_by_status(self, status: str) -> int:
        return self.count(AgentTask.status == status)
