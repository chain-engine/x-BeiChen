#!/usr/bin/env python3
"""数据监控 Agent 子图节点（北辰 x-BeiChen）。

子图步骤（）：
    pull（拉取数据）→ calc（计算指标）→ judge（判定异常）
        └─ 条件边：normal → END（正常，回到拉取进入下一轮）
                  alert → alert（异常，告警 + 建议 + 发布事件）

节点职责边界：只负责"干"（数据获取/计算/判定/告警），不负责"派给谁"（顶层编排管）。
业务规则集中在 monitor/policy.py，事件构造走 agents/events.py 的 build_event。
"""

from __future__ import annotations

from typing import Any

from src.agents.approval import build_money_suggestion
from src.agents.events import build_event
from src.agents.monitor.policy import BUDGET_USAGE_ALERT_THRESHOLD
from src.agents.monitor.state import MonitorState
from src.agents.tools.registry import tool_registry
from src.constants import EventType, TaskStatus, ToolPermissionLevel
from src.core.logger import logger


def pull_data_node(state: MonitorState) -> dict[str, Any]:
    """步骤 1：拉取广告投放数据（只读工具）。"""
    payload = state.get("payload") or {}
    account_id = payload.get("account_id", "acc_default")
    campaign_id = payload.get("campaign_id")
    raw = tool_registry.invoke(
        "ads.get_campaign_stats",
        account_id=account_id,
        campaign_id=campaign_id,
    )
    logger.info(f"[Monitor] pull: account={account_id} raw={raw}")
    return {"raw": raw}


def calc_metric_node(state: MonitorState) -> dict[str, Any]:
    """步骤 2：计算指标（消耗 / 转化 / 成本效率）。"""
    raw = state.get("raw") or {}
    cost = float(raw.get("cost", 0))
    conversions = int(raw.get("conversions", 0))
    clicks = int(raw.get("clicks", 0))
    budget = float(raw.get("budget", 1))
    metric = {
        "cost": cost,
        "conversions": conversions,
        "cpc": round(cost / clicks, 2) if clicks else 0.0,
        "cv_rate": round(conversions / clicks * 100, 2) if clicks else 0.0,
        "budget_usage_rate": round(cost / budget * 100, 2) if budget else 0.0,
    }
    logger.info(f"[Monitor] calc: {metric}")
    return {"metric": metric}


def judge_node(state: MonitorState) -> dict[str, Any]:
    """步骤 3：判定异常（阈值规则）。"""
    metric = state.get("metric") or {}
    anomaly = False
    suggestion: dict[str, Any] | None = None
    usage = metric.get("budget_usage_rate", 0)
    if usage > BUDGET_USAGE_ALERT_THRESHOLD:
        anomaly = True
        suggestion = build_money_suggestion(
            suggestion_type="budget_alert",
            message=f"预算消耗已达 {usage}%，建议关注消耗节奏",
        )
    logger.info(f"[Monitor] judge: anomaly={anomaly} suggestion={suggestion}")
    # normal / alert 两条分支都在此结束判定并把状态归一化为 success：
    # normal → END（不经过 alert_node），必须显式回写 status，否则顶层状态
    # 会停留在 runtime 初始的 running，任务落库后永远显示"执行中"。
    return {
        "anomaly": anomaly,
        "suggestion": suggestion,
        "status": TaskStatus.SUCCESS.mark,
    }


def alert_node(state: MonitorState) -> dict[str, Any]:
    """步骤 4：告警 + 建议 + 发布事件（异常分支）。

    资金铁律：涉及资金写操作（调预算/暂停）Agent 不直接调用审批写工具，
    而是发布 SUGGESTION_CREATED 事件，由审批流程（二期）接手创建审批单。
    """
    suggestion = state.get("suggestion") or {}
    events = list(state.get("events") or [])
    # 1. 即时告警（只读工具，Agent 可直接调用）
    tool_registry.invoke(
        "notification.send_alert",
        channel="ops",
        title="广告投放异常告警",
        content=suggestion.get("message", "检测到投放异常"),
        campaign_id=(state.get("raw") or {}).get("campaign_id"),
    )
    # 2. 发布双事件（口径约定）：
    #    ALERT_RAISED      即时告警事实 → 管理后台「告警面板」消费
    #    SUGGESTION_CREATED 处置建议单（涉及资金写）→ 审批闸门消费（二期）
    events.append(build_event(EventType.ALERT_RAISED, "monitor", payload={"metric": state.get("metric"), "suggestion": suggestion}))
    events.append(build_event(EventType.SUGGESTION_CREATED, "monitor", payload=suggestion))
    result = {
        "metric": state.get("metric"),
        "suggestion": suggestion,
        "approved_actions": [],  # 审批通过后的执行记录（二期回填）
    }
    logger.info(f"[Monitor] alert published, events={len(events)}")
    return {"events": events, "result": result, "status": TaskStatus.SUCCESS.mark}
