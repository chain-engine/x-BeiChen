#!/usr/bin/env python3
"""数据监控 Agent 业务策略（阈值、告警文案、建议结构）。

节点函数只负责"读状态 → 调策略 → 返回结果"，具体规则集中在此，
业务调整改这里即可，不动图结构和节点流程。
"""

from __future__ import annotations

# 预算消耗率告警阈值（%）：mock 演示用，业务接入后改规则库/RAG
BUDGET_USAGE_ALERT_THRESHOLD: float = 60.0


def build_budget_alert_suggestion(usage: float) -> dict:
    """构造"预算消耗过快"的处置建议（涉及资金写 → 走审批，Agent 不直接执行）。"""
    return {
        "type": "budget_alert",
        "message": f"预算消耗已达 {usage}%，建议关注消耗节奏",
        "involves_money": True,
    }
