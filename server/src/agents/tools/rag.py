#!/usr/bin/env python3
"""RAG 知识检索工具包（北辰 x-BeiChen）。

商务对话 Agent 回答政策 / 合作规则 / FAQ 的知识底座。
骨架阶段返回 mock 知识片段；对接真实知识库时：
    1. 文档入库：embedding 向量化 → 向量库（Milvus / pgvector）
    2. 检索：query embedding → 向量相似度 Top-K → 组装上下文
    3. 引用溯源：每条回复携带知识来源（证据可追溯，避免 Agent 瞎编）
"""

from __future__ import annotations

from typing import Any

from src.agents.tools.registry import ToolSpec, tool_registry
from src.constants import ToolPermissionLevel
from src.core.logger import logger

# 骨架阶段的 mock 知识库（二期替换为向量库检索）
_MOCK_KNOWLEDGE: list[dict[str, str]] = [
    {"id": "P001", "title": "合作政策：准入条件", "content": "合作方需具备合法广告投放资质，历史消耗达标后方可开通 API 对接。"},
    {"id": "P002", "title": "合作政策：分成比例", "content": "标准分成为媒体侧 30%，广告主侧 70%，阶梯返点按月度消耗计算。"},
    {"id": "P003", "title": "FAQ：结算周期", "content": "月度结算，次月 10 日出账单，15 日前完成打款。"},
    {"id": "P004", "title": "FAQ：预算调整", "content": "预算调整需在系统提交申请，人工审批通过后生效，资金操作全程留痕。"},
]


def retrieve(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """知识检索（只读）：按 query 返回 Top-K 知识片段。

    TODO(业务接入): embedding + 向量库相似度检索，替换 mock 命中。
    """
    logger.info(f"[RAG] retrieve query={query} top_k={top_k}")
    # mock 命中：按关键词简单打分（仅骨架演示）
    query_lower = query.lower()
    scored = []
    for item in _MOCK_KNOWLEDGE:
        score = sum(1 for kw in query_lower.split() if kw in item["title"].lower() or kw in item["content"].lower())
        scored.append({**item, "score": 1.0 if score else 0.0})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def register_rag_tools() -> None:
    """注册 RAG 工具（幂等）。"""
    if tool_registry.get("rag.retrieve") is None:
        tool_registry.register(ToolSpec(name="rag.retrieve", description="检索公司政策/FAQ 知识（只读）", func=retrieve, permission_level=ToolPermissionLevel.READ_ONLY))


register_rag_tools()

__all__ = ["retrieve", "register_rag_tools"]
