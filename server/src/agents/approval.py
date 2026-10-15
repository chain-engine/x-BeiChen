#!/usr/bin/env python3
"""资金类写操作审批策略（铁律收口）。

"涉及资金的写操作 Agent 不直接执行，只生成审批单，由审批通过后的执行器落地"
这条规则原来散落在 monitor judge_node、alert_node、ads.py 三处，
统一到这里，改一次全生效。
"""

from __future__ import annotations

# 涉及资金的动作清单（写操作，必须走审批闸门）
MONEY_RELATED_ACTIONS: frozenset[str] = frozenset({
    "adjust_budget",
    "pause_campaign",
    "resume_campaign",
})


def involves_money(action: str) -> bool:
    """判断某动作是否涉及资金写操作。"""
    return action in MONEY_RELATED_ACTIONS


def build_money_suggestion(suggestion_type: str, message: str, **extra) -> dict:
    """构造涉及资金的处置建议（标记 involves_money，下游审批闸门消费）。"""
    return {
        "type": suggestion_type,
        "message": message,
        "involves_money": True,
        **extra,
    }
