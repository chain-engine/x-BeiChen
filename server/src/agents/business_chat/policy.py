#!/usr/bin/env python3
"""商务对话 Agent 业务策略（意图关键词、回复模板）。"""

from __future__ import annotations

# 命中即转人工的关键词（mock 规则，业务接入后改 LLM 意图分类）
HUMAN_REQUIRED_KEYWORDS: tuple[str, ...] = ("人工", "投诉", "退款", "经理")

CONSULT_POLICY_INTENT = "consult_policy"
HUMAN_REQUIRED_INTENT = "human_required"


def classify_intent(message: str) -> str:
    """轻量意图分类：命中人工关键词转人工，否则默认咨询政策。"""
    if any(kw in message for kw in HUMAN_REQUIRED_KEYWORDS):
        return HUMAN_REQUIRED_INTENT
    return CONSULT_POLICY_INTENT
