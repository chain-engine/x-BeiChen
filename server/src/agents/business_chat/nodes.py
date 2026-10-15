#!/usr/bin/env python3
"""商务对话 Agent 子图节点（北辰 x-BeiChen）。

子图步骤：
    intent（意图识别）→ retrieve（RAG 检索）→ generate（生成回复）
        └─ 条件边：need_human → transfer（转人工 + interrupt 接管点）
                  normal → END

LLM provider 通过 generate_node_factory 闭包注入，节点函数本身不再 import infras，
便于测试 mock 与切换实现。
"""

from __future__ import annotations

from typing import Any

from langgraph.types import interrupt

from src.agents.business_chat.policy import CONSULT_POLICY_INTENT, classify_intent
from src.agents.business_chat.state import ChatState
from src.agents.events import build_event
from src.agents.tools.registry import tool_registry
from src.constants import EventType, TaskStatus, ToolPermissionLevel
from src.core.logger import logger


def classify_intent_node(state: ChatState) -> dict[str, Any]:
    """步骤 1：意图识别（规则见 policy.py）。"""
    message = (state.get("payload") or {}).get("message", "")
    customer_id = (state.get("payload") or {}).get("customer_id")
    intent = classify_intent(message)
    logger.info(f"[Chat] intent: {intent} customer={customer_id}")
    return {"intent": intent, "message": message, "customer_id": customer_id}


def retrieve_node(state: ChatState) -> dict[str, Any]:
    """步骤 2：RAG 知识检索（政策 / 合作规则 / FAQ，带来源溯源）。"""
    query = state.get("message") or ""
    knowledge = tool_registry.invoke(
        "rag.retrieve",
        ToolPermissionLevel.READ_ONLY,
        query=query,
        top_k=3,
    )
    logger.info(f"[Chat] retrieve: {len(knowledge)} 条知识")
    return {"knowledge": knowledge}


def generate_node_factory(llm_provider: Any) -> Any:
    """generate 节点工厂：闭包捕获 llm_provider，节点签名保持 (state) -> dict。"""

    def generate_node(state: ChatState) -> dict[str, Any]:
        """步骤 3：生成回复。

        - 意图为 human_required → interrupt() 暂停等待人工（LangGraph 断点续跑）
        - 正常意图 → 基于 RAG 知识生成回复；provider 返回 None model 时走 mock 回复
        """
        if state.get("intent") == "human_required":
            human_request = interrupt(
                {
                    "reason": "客户请求人工介入",
                    "customer_id": state.get("customer_id"),
                    "message": state.get("message"),
                }
            )
            logger.info(f"[Chat] interrupt 恢复，人工决策: {human_request}")
            reply = f"已为您转接人工客服（人工备注：{human_request}）。"
            return {
                "need_human": True,
                "reply": reply,
                "result": {"reply": reply, "intent": "human_required", "handled_by": "human"},
                "status": TaskStatus.SUCCESS.mark,
            }

        knowledge = state.get("knowledge") or []
        sources = [item.get("id") for item in knowledge]

        model = llm_provider.get_chat_model()
        if model is not None:
            from langchain_core.prompts import ChatPromptTemplate

            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", "你是广告联盟商务助手。只依据提供的知识回答，引用来源编号，不确定就说不知道。"),
                    ("human", "客户问题：{question}\n知识库：{knowledge}"),
                ]
            )
            chain = prompt | model
            response = chain.invoke(
                {"question": state.get("message"), "knowledge": knowledge or "（无匹配知识）"}
            )
            reply = str(response.content)
        else:
            reply = f"【mock 回复】已收到您的咨询，可参考：{'; '.join(k.get('title', '') for k in knowledge) or '暂无匹配政策'}。"

        events = list(state.get("events") or [])
        if state.get("intent") in (CONSULT_POLICY_INTENT,):
            events.append(
                build_event(
                    EventType.INTENT_DETECTED,
                    "business_chat",
                    payload={"customer_id": state.get("customer_id"), "intent": state.get("intent")},
                )
            )
        logger.info(f"[Chat] generate reply done, sources={sources}")
        return {
            "reply": reply,
            "need_human": False,
            "events": events,
            "result": {"reply": reply, "sources": sources, "intent": state.get("intent")},
            "status": TaskStatus.SUCCESS.mark,
        }

    return generate_node


def transfer_node(state: ChatState) -> dict[str, Any]:
    """步骤 4：转人工（need_human 分支）。"""
    events = list(state.get("events") or [])
    events.append(
        build_event(
            EventType.INTENT_DETECTED,
            "business_chat",
            payload={"customer_id": state.get("customer_id"), "need_human": True},
        )
    )
    logger.info(f"[Chat] transfer to human, customer={state.get('customer_id')}")
    return {
        "events": events,
        "status": TaskStatus.SUCCESS.mark,
    }
