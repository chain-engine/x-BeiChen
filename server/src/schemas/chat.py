#!/usr/bin/env python3
"""商务对话域 Schema（business_chat Agent：发消息 / 人工接管回复）。

专属入口在通用任务提交之上做语义封装：调用方只关心"发一句咨询 / 人工回一句"，
无需自己拼 task_type 与 payload；底层仍走 AgentTaskService 提交 business_chat 任务。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatSendIn(BaseModel):
    """客户咨询消息入参（POST /chat/send）。"""

    message: str = Field(..., min_length=1, description="客户消息文本（用于意图识别与 RAG 问答）")
    customer_id: str | None = Field(default=None, description="客户 ID（事件关联用，可空）")


class ChatHumanReplyIn(BaseModel):
    """人工接管回复入参（POST /chat/{task_id}/human-reply）。

    对应 interrupt 暂停后的 resume：人工决策 + 备注，框架从检查点续跑。
    """

    decision: str = Field(default="approve", pattern="^(approve|reject|adjust)$", description="人工决策：approve / reject / adjust")
    remark: str | None = Field(default=None, description="人工备注 / 回复内容")
    extra: dict[str, Any] = Field(default_factory=dict, description="附加数据（透传给 resume）")


def chat_view(task: Any) -> dict[str, Any]:
    """business_chat 任务实体 → 对话视图（回复 / 来源 / 等待人工上下文）。

    - success：reply + sources + intent
    - waiting_human：reply 为空，interrupt 携带人工接管上下文（reason/customer_id/message）
    """
    result = task.result or {}
    return {
        "task_id": task.id,
        "status": task.status,
        "thread_id": task.thread_id,
        "reply": result.get("reply"),
        "intent": result.get("intent"),
        "sources": result.get("sources"),
        "interrupt": result.get("interrupt"),
    }


__all__ = ["ChatSendIn", "ChatHumanReplyIn", "chat_view"]
