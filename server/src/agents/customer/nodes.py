#!/usr/bin/env python3
"""客户管理 + 任务调度 Agent 子图节点（北辰 x-BeiChen）。

功能性 Agent 主线（对齐客户原始需求：跟进客户状态 / 定时任务 / 自动出报表）：
    fetch（拉取客户状态快照）→ evaluate（跟进判定）→ compose（编排任务）
        → dispatch（确定性执行 + 事件发布 + 落库）

节点职责边界：只负责"干"（拉取/判定/编排/执行），不负责"派给谁"（顶层编排管）。
铁律约定：
    - 跟进判定 / 报表 = 确定性规则（policy），不走 LLM 自由生成
    - 跟进记录确定性写（走 CustomerService，不经工具中心）
    - 客户数据管理（CRUD / 状态迁移 / 续约审批）不在本 Agent 职责内（二期 CRM 模块）
业务规则集中在 customer/policy.py，事件构造走 agents/events.py 的 build_event。
"""

from __future__ import annotations

from typing import Any

from src.agents.customer.policy import build_followup_actions, build_full_report_sections, build_report_sections
from src.agents.events import build_event
from src.agents.tools.registry import tool_registry
from src.agents.tools.report import render_report
from src.constants import EventType, TaskStatus, ToolPermissionLevel
from src.core.config import settings
from src.core.logger import logger


def fetch_customers_node(state: dict[str, Any]) -> dict[str, Any]:
    """步骤 1：拉取客户状态快照（DB 可用读真实客户，否则 mock，保证离线自检）。"""
    payload = state.get("payload") or {}
    scope = payload.get("scope", "due_followup")
    customer_ids = payload.get("customer_ids")

    if settings.database.enabled:
        # 真实库：读客户状态（功能性 Agent 的"跟进客户状态"数据源）
        from src.infras.database import get_cached_database_provider
        from src.services.customer_service import CustomerService

        provider = get_cached_database_provider()
        with provider.session() as session:
            service = CustomerService(session)
            if scope == "due_followup":
                customers = service.list_due_followup_snapshots()
            elif scope == "by_ids" and customer_ids:
                customers = service.list_snapshots_by_ids(customer_ids)
            else:
                customers = service.list_all_snapshots()
    else:
        # 离线自检：工具 mock 快照
        if scope == "due_followup":
            customers = tool_registry.invoke("crm.list_due_followup_snapshots", ToolPermissionLevel.READ_ONLY)
        elif scope == "by_ids" and customer_ids:
            customers = tool_registry.invoke("crm.list_customer_snapshots_by_ids", ToolPermissionLevel.READ_ONLY, customer_ids=customer_ids)
        else:
            customers = tool_registry.invoke("crm.list_all_customer_snapshots", ToolPermissionLevel.READ_ONLY)
    logger.info(f"[Customer] fetch: scope={scope} customers={len(customers)} db={settings.database.enabled}")
    return {"customers": customers, "scope": scope}


def evaluate_status_node(state: dict[str, Any]) -> dict[str, Any]:
    """步骤 2：跟进判定 → 动作清单（policy.build_followup_actions 规则引擎）。"""
    customers = state.get("customers") or []
    actions: list[dict[str, Any]] = []
    for c in customers:
        actions.extend(build_followup_actions(c))
    logger.info(f"[Customer] evaluate: actions={len(actions)}")
    return {"actions": actions}


def compose_tasks_node(state: dict[str, Any]) -> dict[str, Any]:
    """步骤 3：动作 → 任务清单（跟进任务 / 报表任务）。

    编排规则：
        - 跟进动作 → followup_tasks（确定性跟进：联系客户）
        - payload.scope=report → 额外生成 report 任务（自动出报表）
    """
    actions = state.get("actions") or []
    scope = state.get("scope", "due_followup")
    followup_tasks: list[dict[str, Any]] = [act for act in actions]

    tasks: list[dict[str, Any]] = [{"kind": "followup", "items": followup_tasks}]
    if scope == "report":
        tasks.append({"kind": "report", "items": [{"action": "report", "reason": "定时报表任务"}]})
    logger.info(f"[Customer] compose: followup={len(followup_tasks)} report={scope == 'report'}")
    return {"tasks": tasks}


def dispatch_node(state: dict[str, Any]) -> dict[str, Any]:
    """步骤 4：确定性执行 + 事件发布 + 落库。

    - 跟进任务 → CustomerService.record_followup（DB 可用时落库；否则仅发事件，自检可离线）
    - 报表任务 → ReportService.generate_report（确定性模板聚合）
    - 事件双写：FOLLOWUP_CREATED / REPORT_GENERATED 全部进 state.events，
      由顶层聚合后统一落库 + publish
    """
    tasks = state.get("tasks") or []
    customers = state.get("customers") or []
    scope = state.get("scope", "due_followup")
    events: list[dict[str, Any]] = []
    executed_followups: list[dict[str, Any]] = []
    report: dict[str, Any] | None = None

    db_available = settings.database.enabled

    for bucket in tasks:
        kind = bucket.get("kind")
        for item in bucket.get("items") or []:
            if kind == "followup":
                # 确定性跟进：DB 可用 → 写 customer_followups；否则仅记录待执行
                executed_followups.append({"customer_id": item.get("customer_id"), "action": item.get("action"), "reason": item.get("reason")})
                events.append(build_event(EventType.FOLLOWUP_CREATED, "customer", payload={
                    "customer_id": item.get("customer_id"),
                    "action": item.get("action"),
                    "reason": item.get("reason"),
                }))
            elif kind == "report":
                # 报表：确定性模板聚合（policy.build_full_report_sections + report.render_report）
                if customers:
                    content = build_full_report_sections(customers, stats_map={})
                else:
                    content = build_report_sections({"customer_id": "?", "name": "无客户"}, stats={})
                rendered = tool_registry.invoke(
                    "report.render_report",
                    ToolPermissionLevel.READ_ONLY,
                    sections=content,
                    title="客户日报",
                )
                report = {"content": content, "rendered": rendered}
                events.append(build_event(EventType.REPORT_GENERATED, "customer", payload={
                    "report_type": "daily",
                    "customers": len(customers),
                    "rendered_preview": rendered[:120],
                }))

    # DB 可用时确定性落库（跟进记录 / 报表产物）；不可用时跳过（骨架离线自检）
    if db_available and executed_followups:
        try:
            _persist_followups(executed_followups)
        except Exception as exc:
            logger.exception(f"[Customer] 跟进落库失败（事件已留痕）：{exc}")

    result = {
        "followups": executed_followups,
        "report": report,
        "db_persisted": db_available,
    }
    logger.info(f"[Customer] dispatch: followups={len(executed_followups)} report={report is not None}")
    return {
        "events": events,
        "result": result,
        "status": TaskStatus.SUCCESS.mark,
    }


def _persist_followups(items: list[dict[str, Any]]) -> None:
    """确定性落库跟进记录（内部：CustomerService.record_followup）。"""
    from src.infras.database import get_cached_database_provider
    from src.services.customer_service import CustomerService

    provider = get_cached_database_provider()
    with provider.session() as session:
        service = CustomerService(session)
        for item in items:
            cid = item.get("customer_id")
            if cid:
                service.record_followup(
                    customer_id=cid,
                    action=item.get("action", "message"),
                    content=item.get("reason", ""),
                    operator="customer",
                )


__all__ = ["fetch_customers_node", "evaluate_status_node", "compose_tasks_node", "dispatch_node"]
