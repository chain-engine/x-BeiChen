#!/usr/bin/env python3
"""客户管理 + 任务调度 Agent 业务策略（跟进判定 / 报表策略）。

功能性 Agent 主线（对齐客户原始需求）：
    1. 跟进客户状态：拉取客户快照 → 判定哪些客户需要跟进（跟进到期 / 沉睡预警 / 合同到期提醒）
    2. 定时任务：周期触发（APScheduler job，见 scheduling/jobs.py）
    3. 自动出报表：模板 + 数据聚合（确定性，可复算、可审计）

职责边界：本模块只做"判定"，不做客户数据管理。
    - 状态迁移 / 客户 CRUD 等客户管理功能 → 二期独立 CRM 模块（本 Agent 只读状态）
    - 合同到期只作为跟进提醒（联系谈续约），续约资金动作由审批闸门（广告审批系统）处理，本 Agent 不生成审批单
业务调整改这里即可，不动图结构和节点流程。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from src.constants import CustomerStatus

# ── 跟进判定阈值（mock，业务接入后改规则库）─────────────────
FOLLOWUP_DUE_DAYS: int = 7                 # 超过 N 天未跟进 → 生成跟进任务
DORMANT_DAYS_THRESHOLD: int = 30           # 活跃后 N 天无跟进 → 沉睡预警
CONTRACT_EXPIRE_WARN_DAYS: int = 30        # 合同剩余 N 天内 → 生成续约跟进提醒

# 跟进动作类型（customer_followups.action，功能性 Agent 产出物）
ACTION_CALL = "call"        # 电话联系
ACTION_VISIT = "visit"      # 上门拜访 / 回访
ACTION_MESSAGE = "message"  # 消息触达（IM / 微信 / 邮件）


def build_followup_actions(
    customer: dict[str, Any],
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """按客户快照（dict）生成跟进动作（evaluate_status 节点的规则引擎）。

    判定顺序：跟进到期 → 沉睡预警 → 合同到期提醒。
    返回结构（供 compose_tasks 消费）：{action, reason, priority, days}。
    """
    now = now or datetime.now(UTC)
    actions: list[dict[str, Any]] = []
    status = customer.get("status", "") or ""
    cid = customer.get("customer_id", "")

    # 1. 跟进到期（next_followup_at 已过 → 需要主动联系）
    next_at = customer.get("next_followup_at")
    if next_at is not None and next_at < now:
        overdue = max((now - next_at).days, 0)
        actions.append({
            "customer_id": cid,
            "action": ACTION_MESSAGE,
            "reason": f"跟进已逾期 {overdue} 天",
            "priority": "normal",
            "days": overdue,
        })

    # 2. 沉睡预警（活跃客户 N 天无跟进 → 回访挽留）
    if status == CustomerStatus.ACTIVE.mark:
        last_at = customer.get("last_followup_at")
        if last_at is not None and (now - last_at).days > DORMANT_DAYS_THRESHOLD:
            actions.append({
                "customer_id": cid,
                "action": ACTION_VISIT,
                "reason": f"已 {DORMANT_DAYS_THRESHOLD}+ 天无跟进，存在沉睡风险",
                "priority": "medium",
                "days": (now - last_at).days,
            })

    # 3. 合同到期提醒（签约/活跃客户 → 安排洽谈续约的跟进动作）
    if status in (CustomerStatus.SIGNED.mark, CustomerStatus.ACTIVE.mark):
        expire_days = customer.get("contract_expire_days")  # mock：二期从合同表读取
        if expire_days is not None and expire_days <= CONTRACT_EXPIRE_WARN_DAYS:
            actions.append({
                "customer_id": cid,
                "action": ACTION_CALL,
                "reason": f"合同剩余 {expire_days} 天到期，安排洽谈续约",
                "priority": "high",
                "days": expire_days,
            })

    return actions


def build_report_sections(customer: dict[str, Any], stats: dict[str, Any] | None = None) -> dict[str, Any]:
    """组装单客户报表的确定性数据段（模板 + 聚合，不做 LLM 自由生成）。

    TODO(业务接入): stats 从广告平台消耗/转化数据聚合（复用 ads.get_campaign_stats）；
    当前用 mock 数据占位，接入后替换为真实聚合即可，结构不变。
    """
    stats = stats or {}
    return {
        "customer_id": customer.get("customer_id", ""),
        "customer_name": customer.get("name", ""),
        "status": customer.get("status", ""),
        "contract_amount": float(customer.get("contract_amount", 0) or 0),
        "budget": float(customer.get("budget", 0) or 0),
        "period_cost": float(stats.get("cost", 0)),
        "period_conversions": int(stats.get("conversions", 0)),
        "summary": "消耗与转化概览（确定性聚合，洞察总结二期由 insight Agent 补充）",
    }


def build_full_report_sections(customers: list[dict[str, Any]], stats_map: dict[str, dict] | None = None) -> dict[str, Any]:
    """组装全量客户报表（日报/周报）：客户维度汇总段。

    TODO(业务接入): stats_map 为 {customer_id: 投放统计}，二期从广告平台聚合。
    """
    stats_map = stats_map or {}
    rows = [build_report_sections(c, stats_map.get(c.get("customer_id", ""))) for c in customers]
    return {
        "total_customers": len(rows),
        "active_customers": sum(1 for r in rows if r["status"] == CustomerStatus.ACTIVE.mark),
        "dormant_customers": sum(1 for r in rows if r["status"] == CustomerStatus.DORMANT.mark),
        "total_contract_amount": round(sum(r["contract_amount"] for r in rows), 2),
        "rows": rows,
    }


def default_next_followup(now: datetime | None = None) -> datetime:
    """默认下次跟进时间（当前 + FOLLOWUP_DUE_DAYS）。"""
    now = now or datetime.now(UTC)
    return now + timedelta(days=FOLLOWUP_DUE_DAYS)


__all__ = [
    "FOLLOWUP_DUE_DAYS",
    "DORMANT_DAYS_THRESHOLD",
    "CONTRACT_EXPIRE_WARN_DAYS",
    "ACTION_CALL",
    "ACTION_VISIT",
    "ACTION_MESSAGE",
    "build_followup_actions",
    "build_report_sections",
    "build_full_report_sections",
    "default_next_followup",
]
