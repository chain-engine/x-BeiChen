#!/usr/bin/env python3
"""商务对话 Agent（对象化门面）。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.agents.base import BaseAgent
from src.agents.business_chat.graph import build_business_chat_graph
from src.constants import AgentType

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


class BusinessChatAgent(BaseAgent):
    """商务对话 Agent：意图识别 → RAG 检索 → 生成回复 / 转人工。"""

    agent_type = AgentType.BUSINESS_CHAT
    name = "商务对话 Agent"
    description = "自动接待客户咨询、RAG 检索政策、生成回复、引导转化、转人工"

    def build(self) -> "CompiledStateGraph":
        return build_business_chat_graph()
