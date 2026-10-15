#!/usr/bin/env python3
"""商务对话 Agent 子图构建（北辰 x-BeiChen）。

    START → intent → retrieve → generate ──normal──▶ END
                                      └──need_human──▶ transfer → END
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langgraph.graph import END, START, StateGraph

from src.agents.business_chat.nodes import (
    classify_intent_node,
    generate_node_factory,
    retrieve_node,
    transfer_node,
)
from src.agents.business_chat.state import ChatState

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


def route_generate(state: ChatState) -> str:
    """条件边路由：生成后是否需要转人工。"""
    return "transfer" if state.get("need_human") else "end"


def build_business_chat_graph(llm_provider: Any | None = None) -> "CompiledStateGraph":
    """构建商务对话 Agent 子图（已编译）。

    Args:
        llm_provider: LLM 提供方；缺省走全局工厂 get_llm_provider()，便于测试传入替身。
    """
    if llm_provider is None:
        from src.infras.llm import get_llm_provider

        llm_provider = get_llm_provider()

    graph = StateGraph(ChatState)
    graph.add_node("intent", classify_intent_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node_factory(llm_provider))
    graph.add_node("transfer", transfer_node)

    graph.add_edge(START, "intent")
    graph.add_edge("intent", "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_conditional_edges(
        "generate",
        route_generate,
        {"transfer": "transfer", "end": END},
    )
    graph.add_edge("transfer", END)

    return graph.compile()


__all__ = ["build_business_chat_graph", "route_generate"]
