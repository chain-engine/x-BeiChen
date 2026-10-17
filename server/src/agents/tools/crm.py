#!/usr/bin/env python3
"""客户管理工具包（北辰 x-BeiChen，客户管理 + 任务调度 Agent）。

功能性 Agent 定位：工具中心只为"跟进客户状态"提供只读查询
（crm.list_customer_snapshots / crm.get_customer_snapshot）。
    - 跟进判定 / 报表由 policy 确定性规则完成（不进工具中心）
    - 客户数据管理（CRUD / 状态迁移 / 续约审批）不在本 Agent 职责内（二期 CRM 模块）

无数据库时降级为 mock 快照，保证编排链路可离线自检（与 ads/rag 同风格）。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from src.agents.tools.registry import ToolSpec, tool_registry
from src.constants import CustomerStatus, ToolPermissionLevel
from src.core.logger import logger


def _build_mock_customers() -> list[dict[str, Any]]:
    """无数据库时的 mock 客户快照（覆盖：跟进到期 / 沉睡 / 合同到期提醒 三类场景）。"""
    now = datetime.now(UTC)
    return [
        {
            "customer_id": "cust_001",
            "name": "演示客户A",
            "industry": "电商",
            "status": CustomerStatus.ACTIVE.mark,
            "contract_amount": 120000.00,
            "budget": 30000.00,
            "next_followup_at": now - timedelta(days=3),   # 跟进已逾期 3 天
            "last_followup_at": now - timedelta(days=45),  # 沉睡预警（>30 天）
            "contract_expire_days": 15,                    # 合同 15 天后到期（跟进提醒：谈续约）
            "assignee": "ops_mock",
        },
        {
            "customer_id": "cust_002",
            "name": "演示客户B",
            "industry": "游戏",
            "status": CustomerStatus.LEAD.mark,
            "contract_amount": 0.0,
            "budget": 0.0,
            "next_followup_at": now - timedelta(days=1),   # 跟进已逾期 1 天
            "last_followup_at": now - timedelta(days=10),
            "assignee": "ops_mock",
        },
    ]


def list_customer_snapshots(scope: str = "full", customer_ids: list[str] | None = None) -> list[dict[str, Any]]:
    """拉取客户快照列表（只读）。

    Args:
        scope: full 全量 / due_followup 跟进到期 / by_ids 指定客户
        customer_ids: scope=by_ids 时传入

    TODO(业务接入): DB 启用时 fetch 节点直接读 CustomerService.snapshot（真实库），
    本工具仅用于离线自检 mock。
    """
    logger.info(f"[Crm] list_customer_snapshots scope={scope} ids={customer_ids}")
    customers = _build_mock_customers()
    if scope == "due_followup":
        now = datetime.now(UTC)
        customers = [c for c in customers if c.get("next_followup_at") and c["next_followup_at"] < now]
    elif scope == "by_ids" and customer_ids:
        customers = [c for c in customers if c.get("customer_id") in customer_ids]
    return customers


def get_customer_snapshot(customer_id: str) -> dict[str, Any] | None:
    """查询单个客户快照（只读）。"""
    logger.info(f"[Crm] get_customer_snapshot id={customer_id}")
    for c in _build_mock_customers():
        if c.get("customer_id") == customer_id:
            return c
    return None


def register_crm_tools() -> None:
    """注册客户管理工具（幂等）。"""
    if tool_registry.get("crm.list_customer_snapshots") is None:
        tool_registry.register(ToolSpec(name="crm.list_customer_snapshots", description="拉取客户快照列表（只读）", func=list_customer_snapshots, permission_level=ToolPermissionLevel.READ_ONLY))
        tool_registry.register(ToolSpec(name="crm.get_customer_snapshot", description="查询单个客户快照（只读）", func=get_customer_snapshot, permission_level=ToolPermissionLevel.READ_ONLY))


register_crm_tools()

__all__ = ["list_customer_snapshots", "get_customer_snapshot", "register_crm_tools"]
