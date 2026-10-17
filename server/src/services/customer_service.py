#!/usr/bin/env python3
"""客户业务服务（北辰 x-BeiChen，客户管理+调度 Agent）。

职责边界（api → services → repositories 单向）：
    - 客户快照：列表 / 单客户查询（供子图 fetch 节点消费——"跟进客户状态"数据源）
    - 跟进记录：写入 customer_followups，更新客户跟进节奏（Agent 产出物落库）

事件不归本服务双写：FOLLOWUP_CREATED 等协作事件由子图写入 state.events，
统一由 AgentTaskService 落库 + EventBus 发布，避免同一事件重复落库/重复广播。

功能性 Agent 定位：本服务为 Agent 主线（跟进客户状态 / 定时任务 / 自动出报表）服务；
客户数据管理（CRUD / 状态迁移 / 续约审批）属二期独立 CRM 模块，不在本服务职责内。
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from src.agents.customer.policy import default_next_followup
from src.constants import EventType
from src.core.exceptions import NotFoundException
from src.core.logger import logger
from src.infras.event_bus import EventBus, EventMessage, get_event_bus
from src.models.entities.agent_event import AgentEvent
from src.models.entities.customer import Customer
from src.models.entities.customer_followup import CustomerFollowup
from src.repositories.customer_repository import CustomerRepository
from src.repositories.customer_followup_repository import CustomerFollowupRepository


def _aware_dt(dt: datetime | None) -> datetime | None:
    """naive MySQL DATETIME 补 UTC 时区（policy 用 aware 时间比较，避免 naive/aware 混用报错）。"""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def to_customer_snapshot(c: Customer) -> dict[str, Any]:
    """ORM Customer → 统一快照 dict（全项目唯一映射，报表/跟进共用同一份字段形态）。

    时区约定：MySQL DATETIME 读出为 naive，统一补 UTC 再交给 policy。
    contract_expire_days 二期从合同表关联计算，当前占位 None。
    """
    return {
        "customer_id": c.customer_id,
        "name": c.name,
        "industry": c.industry,
        "status": c.status,
        "contract_amount": float(c.contract_amount or 0),
        "budget": float(c.budget or 0),
        "next_followup_at": _aware_dt(c.next_followup_at),
        "last_followup_at": _aware_dt(c.last_followup_at),
        "assignee": c.assignee,
        "contract_expire_days": None,  # TODO(业务接入): 合同表关联计算
    }


class CustomerService:
    """客户业务服务：快照 / 跟进记录（功能性 Agent 主线）。"""

    def __init__(self, session: Session, event_bus: EventBus | None = None) -> None:
        self._session = session
        self._repo = CustomerRepository(session)
        self._followup_repo = CustomerFollowupRepository(session)
        self._event_bus: EventBus = event_bus or get_event_bus()

    # ----------------------------------------------------------
    # 客户状态查询（"跟进客户状态"数据源）
    # ----------------------------------------------------------

    def list_customers(self, status: str | None = None, page: int = 1, page_size: int = 20) -> tuple[list[Customer], int]:
        offset = (page - 1) * page_size
        if status:
            items = self._repo.list_by_status(status, offset=offset, limit=page_size)
            total = self._repo.count(Customer.status == status)
        else:
            items = self._repo.list(order_by=self._repo.model_class.id.desc(), offset=offset, limit=page_size)
            total = self._repo.count()
        return items, total

    def get_customer(self, customer_id: str) -> Customer:
        c = self._repo.get_by_customer_id(customer_id)
        if c is None:
            raise NotFoundException(f"客户不存在：{customer_id}")
        return c

    def list_all_snapshots(self, limit: int = 100) -> list[dict[str, Any]]:
        """全量客户快照（供子图 fetch / API 消费）。"""
        customers = self._repo.list_all(limit=limit)
        return [to_customer_snapshot(c) for c in customers]

    def list_due_followup_snapshots(self, limit: int = 100) -> list[dict[str, Any]]:
        """跟进到期客户快照（供子图 fetch / API 消费）。

        TODO(业务接入): contract_expire_days 二期从合同表关联计算。
        """
        customers = self._repo.list_due_followup(now=datetime.now(UTC), limit=limit)
        return [to_customer_snapshot(c) for c in customers]

    def list_snapshots_by_ids(self, customer_ids: list[str]) -> list[dict[str, Any]]:
        """按客户 ID 列表获取快照（供子图 fetch / API 消费）。"""
        customers = [c for cid in customer_ids if (c := self._repo.get_by_customer_id(cid)) is not None]
        return [to_customer_snapshot(c) for c in customers]

    def get_snapshot(self, customer_id: str) -> dict[str, Any]:
        c = self._repo.get_by_customer_id(customer_id)
        if c is None:
            raise NotFoundException(f"客户不存在：{customer_id}")
        return to_customer_snapshot(c)

    # ----------------------------------------------------------
    # 跟进记录（确定性写，Agent 产出物落库）
    # ----------------------------------------------------------

    def record_followup(
        self,
        customer_id: str,
        action: str,
        content: str = "",
        operator: str = "customer",
        next_followup_at: datetime | None = None,
    ) -> CustomerFollowup:
        """写入跟进记录并刷新客户跟进节奏。"""
        c = self._repo.get_by_customer_id(customer_id)
        if c is None:
            raise NotFoundException(f"客户不存在：{customer_id}")
        followup = CustomerFollowup(
            customer_id=customer_id,
            action=action,
            content=content or f"跟进动作：{action}",
            operator=operator,
            next_followup_at=next_followup_at or default_next_followup(),
        )
        self._followup_repo.add(followup)
        c.last_followup_at = datetime.now(UTC)
        c.next_followup_at = followup.next_followup_at

        # 客户域事件双写：agent_events 落库 + EventBus publish（失败仅记日志）
        payload = {
            "customer_id": customer_id,
            "action": action,
            "content": followup.content,
        }
        self._session.add(AgentEvent(
            event_type=EventType.FOLLOWUP_CREATED,
            source_agent="customer",
            target_agent=None,
            payload=payload,
            status="recorded",
        ))
        try:
            import asyncio

            # 有 running loop（FastAPI 请求上下文）→ create_task 异步发布；
            # 无 loop（线程池/脚本）→ asyncio.run 同步发布。
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop is not None:
                loop.create_task(self._event_bus.publish(EventMessage(event_type=EventType.FOLLOWUP_CREATED, payload=payload, source_agent="customer", target_agent=None)))
            else:
                asyncio.run(self._event_bus.publish(EventMessage(event_type=EventType.FOLLOWUP_CREATED, payload=payload, source_agent="customer", target_agent=None)))
        except Exception as exc:
            logger.exception(f"[CustomerService] 事件发布失败（已落库留痕）：{exc}")

        self._repo.commit()
        logger.info(f"[CustomerService] 跟进记录 {customer_id}: {action}")
        return followup

    def list_followups(self, customer_id: str, page: int = 1, page_size: int = 20) -> tuple[list[CustomerFollowup], int]:
        offset = (page - 1) * page_size
        items = self._followup_repo.list_by_customer(customer_id, offset=offset, limit=page_size)
        total = self._followup_repo.count(CustomerFollowup.customer_id == customer_id)
        return items, total


__all__ = ["CustomerService", "to_customer_snapshot"]

