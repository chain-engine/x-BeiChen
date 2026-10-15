#!/usr/bin/env python3
"""商务对话 Agent 子图节点（北辰 x-BeiChen）。

子图步骤：
    intent（意图识别）→ retrieve（RAG 检索）→ generate（生成回复）
        └─ 条件边：need_human → transfer（转人工 + interrupt 接管点）
                  normal → END

LangChain 配合的标准姿势（generate 节点）：
    ChatPromptTemplate（prompt 模板）│ ChatOpenAI（模型）→ 链式调用。
    API Key 未配置时走 mock 分支（get_chat_model() 返回 None），骨架可独立运行。
"""

from __future__ import annotations

from typing import Any

from langgraph.types import interrupt

from src.agents.business_chat.state import ChatState
from src.agents.tools import retrieve
from src.constants import EventType, TaskStatus
from src.core.logger import logger


def classify_intent_node(state: ChatState) -> dict[str, Any]:
    """步骤 1：意图识别。

    TODO(业务接入): 用 ChatPromptTemplate + LLM 做意图分类（few-shot），
    兜底规则命中（含"人工""投诉""退款"等词 → need_human=True）。
    """
    message = (state.get("payload") or {}).get("message", "")
    customer_id = (state.get("payload") or {}).get("customer_id")
    intent = "consult_policy"  # mock：默认咨询政策
    if any(kw in message for kw in ("人工", "投诉", "退款", "经理")):
        intent = "human_required"
    logger.info(f"[Chat] intent: {intent} customer={customer_id}")
    return {"intent": intent, "message": message, "customer_id": customer_id}


def retrieve_node(state: ChatState) -> dict[str, Any]:
    """步骤 2：RAG 知识检索（政策 / 合作规则 / FAQ，带来源溯源）。

    TODO(业务接入): 知识库向量化（Milvus）+ embedding 检索，替换 mock。
    """
    query = state.get("message") or ""
    knowledge = retrieve(query, top_k=3)
    logger.info(f"[Chat] retrieve: {len(knowledge)} 条知识")
    return {"knowledge": knowledge}


def generate_node(state: ChatState) -> dict[str, Any]:
    """步骤 3：生成回复（LangChain prompt + 模型链式调用）。

    - 意图为 human_required → interrupt() 暂停等待人工（LangGraph 断点续跑）
    - 正常意图 → 基于 RAG 知识生成回复；API Key 未配置时返回 mock 回复
    """
    if state.get("intent") == "human_required":
        # 人工接管点：暂停执行，等待 runtime.resume_task(thread_id, decision) 恢复
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

    from src.infras.llm import get_llm_provider

    provider = get_llm_provider()
    model = provider.get_chat_model()
    if model is not None:
        # 标准姿势：ChatPromptTemplate │ ChatOpenAI
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
    if state.get("intent") in ("consult_policy", "join_cooperation"):
        events.append(
            {
                "type": EventType.INTENT_DETECTED,
                "source": "business_chat",
                "payload": {"customer_id": state.get("customer_id"), "intent": state.get("intent")},
            }
        )
    logger.info(f"[Chat] generate reply done, sources={sources}")
    return {
        "reply": reply,
        "need_human": False,
        "events": events,
        "result": {"reply": reply, "sources": sources, "intent": state.get("intent")},
        "status": TaskStatus.SUCCESS.mark,
    }


def transfer_node(state: ChatState) -> dict[str, Any]:
    """步骤 4：转人工（need_human 分支）。

    TODO(业务接入): 对接客服工单系统 / 消息推送，记录人工跟进上下文。
    """
    events = list(state.get("events") or [])
    events.append(
        {
            "type": EventType.INTENT_DETECTED,
            "source": "business_chat",
            "payload": {"customer_id": state.get("customer_id"), "need_human": True},
        }
    )
    logger.info(f"[Chat] transfer to human, customer={state.get('customer_id')}")
    return {
        "events": events,
        "status": TaskStatus.SUCCESS.mark,
    }
