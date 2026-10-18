#!/usr/bin/env python3
"""客户管理 Agent 子图节点（北辰 x-BeiChen，演示实现）。

当前定位：**演示 Agent**（骨架期，详细业务需求尚未定稿）——四个步骤保留标准
结构（fetch → evaluate → compose → dispatch），每步只产出演示数据并打日志，
**不做真实业务动作**（不读库 / 不真实判定 / 不落库 / 不发业务事件）。

业务接入：按各节点 TODO(业务接入) 逐节点替换为真实实现，状态契约（customers /
actions / tasks / result / events / status）与顶层编排保持不变，无需改编排层。

任务调度：周期触发由 APScheduler 外部 job 经 AgentTaskService.submit_task 提交
（本子图不做自循环，与 monitor 一致）。
"""

from __future__ import annotations

from typing import Any

from src.constants import TaskStatus
from src.core.logger import logger

# ── 演示数据（业务接入后删除，改从真实数据源拉取）──────────────


def _demo_customers() -> list[dict[str, Any]]:
    """演示客户快照（fetch 节点产出）。"""
    return [
        {
            "customer_id": "demo_001",
            "name": "演示客户A",
            "industry": "零售",
            "status": "active",
            "contract_amount": 50000,
            "budget": 20000,
            "assignee": "demo_ops",
            "_demo": True,
        },
        {
            "customer_id": "demo_002",
            "name": "演示客户B",
            "industry": "游戏",
            "status": "lead",
            "contract_amount": 0,
            "budget": 5000,
            "assignee": "demo_ops",
            "_demo": True,
        },
    ]


# ── 四步节点（演示）──────────────────────────────────


def fetch_customers_node(state: dict[str, Any]) -> dict[str, Any]:
    """步骤 1/4：拉取客户状态快照（演示）。

    TODO(业务接入): 替换为真实数据源——DB 可用时走 CustomerService.snapshot
    （scope=due_followup / by_ids / full），离线走 crm 工具 mock。
    """
    payload = state.get("payload") or {}
    scope = payload.get("scope", "due_followup")
    customers = _demo_customers()
    logger.info(f"[Customer][演示] 步骤1/4 fetch：返回演示客户快照 {len(customers)} 条（scope={scope}）")
    return {"customers": customers, "scope": scope}


def evaluate_status_node(state: dict[str, Any]) -> dict[str, Any]:
    """步骤 2/4：跟进判定 → 动作清单（演示）。

    TODO(业务接入): 替换为真实判定——policy.build_followup_actions（跟进到期 →
    message / 沉睡预警 → visit / 合同到期 → call 提醒），当前统一给演示动作。
    """
    customers = state.get("customers") or []
    actions = [
        {
            "customer_id": c["customer_id"],
            "action": "message",
            "reason": "演示跟进动作（业务接入后由 policy 规则判定）",
            "_demo": True,
        }
        for c in customers
    ]
    logger.info(f"[Customer][演示] 步骤2/4 evaluate：生成演示动作 {len(actions)} 条")
    return {"actions": actions}


def compose_tasks_node(state: dict[str, Any]) -> dict[str, Any]:
    """步骤 3/4：动作 → 任务清单（演示）。

    TODO(业务接入): 替换为真实编排——跟进动作 → followup_tasks；scope=report
    时追加报表任务（自动出报表）。
    """
    actions = state.get("actions") or []
    scope = state.get("scope", "due_followup")
    followup_tasks = [dict(act) for act in actions]

    tasks: list[dict[str, Any]] = [{"kind": "followup", "items": followup_tasks, "_demo": True}]
    if scope == "report":
        tasks.append({"kind": "report", "items": [{"action": "report", "reason": "演示报表任务（业务接入后由 ReportService 生成）"}], "_demo": True})
    logger.info(f"[Customer][演示] 步骤3/4 compose：跟进任务={len(followup_tasks)} 报表任务={scope == 'report'}")
    return {"tasks": tasks}


def dispatch_node(state: dict[str, Any]) -> dict[str, Any]:
    """步骤 4/4：确定性执行 + 事件 + 落库（演示：不执行 / 不落库 / 不发业务事件）。

    TODO(业务接入): 替换为真实执行——
        跟进任务 → CustomerService.record_followup 落库 + FOLLOWUP_CREATED 事件双写；
        报表任务 → ReportService.generate_report 落库 + REPORT_GENERATED 事件双写。
    """
    tasks = state.get("tasks") or []
    followups: list[dict[str, Any]] = []
    for bucket in tasks:
        if bucket.get("kind") == "followup":
            for item in bucket.get("items") or []:
                followups.append(
                    {
                        "customer_id": item.get("customer_id"),
                        "action": item.get("action"),
                        "reason": item.get("reason"),
                        "_demo": True,
                    }
                )
    result: dict[str, Any] = {
        "followups": followups,
        "report": None,
        "demo": True,
        "note": "演示模式：未落库、未发业务事件，业务接入后由 CustomerService / ReportService 真实执行",
    }
    logger.info(f"[Customer][演示] 步骤4/4 dispatch：演示产出 followups={len(followups)}（未落库 / 未发事件）")
    return {
        "events": [],  # 演示模式不发业务事件（避免污染 agent_events 审计）
        "result": result,
        "status": TaskStatus.SUCCESS.mark,
    }


__all__ = ["fetch_customers_node", "evaluate_status_node", "compose_tasks_node", "dispatch_node"]
