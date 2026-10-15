#!/usr/bin/env python3
"""商务对话 Agent 子图状态（北辰 x-BeiChen）。"""

from __future__ import annotations

from typing import Any

from src.agents.state import AgentTaskState


class ChatState(AgentTaskState):
    """商务对话子图状态。"""

    # ── 对话域私有字段 ──
    customer_id: str | None                     # 客户标识
    message: str | None                         # 用户消息
    intent: str | None                          # 意图识别结果（咨询政策/合作接入/投诉等）
    knowledge: list[dict[str, Any]] | None      # RAG 检索到的知识片段（带来源）
    draft: str | None                           # 生成草稿
    reply: str | None                           # 最终回复
    need_human: bool                            # 是否需要转人工（触发 interrupt 接管点）
