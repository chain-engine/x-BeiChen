#!/usr/bin/env python3
"""商务对话 Agent 对外接口（北辰 x-BeiChen）。

在通用任务提交（POST /tasks）之上提供语义化入口，调用方无需自行拼 task_type：

    POST /chat/send                 发送客户咨询消息（intent → RAG → generate）
                                    命中人工关键词时进入 waiting_human（interrupt 暂停）
    POST /chat/{task_id}/human-reply 人工接管回复（resume 续跑）

数据流向：api 层（本文件）→ services（AgentTaskService）→ AgentRuntime（business_chat 子图）。
通用任务查询 / 事件列表仍走 agents 路由（/tasks、/events）。
"""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import JSONResponse

from src.api.dependencies import get_task_service
from src.api.response import success_response
from src.constants import AgentType
from src.schemas.chat import ChatHumanReplyIn, ChatSendIn, chat_view
from src.services.agent_task_service import AgentTaskService

router = APIRouter(prefix="/chat", tags=["商务对话 Agent"])


@router.post("/send", summary="发送客户咨询消息")
async def send_message(
    request: Request,
    body: ChatSendIn = Body(default=...),
    service: AgentTaskService = Depends(get_task_service),
) -> JSONResponse:
    """提交一条商务对话消息，同步返回机器人回复；命中人工关键词则转入 waiting_human。"""
    task = await service.submit_task(
        task_type=AgentType.BUSINESS_CHAT.mark,
        payload={"message": body.message, "customer_id": body.customer_id},
    )
    return success_response(data=chat_view(task), request=request)


@router.post("/{task_id}/human-reply", summary="人工接管回复")
async def human_reply(
    task_id: int,
    request: Request,
    body: ChatHumanReplyIn = Body(default=...),
    service: AgentTaskService = Depends(get_task_service),
) -> JSONResponse:
    """人工接管：恢复被 interrupt 暂停的对话任务并返回人工回复结果。"""
    task = await service.resume_task(
        task_id=task_id,
        decision=body.decision,
        remark=body.remark,
        extra=body.extra,
    )
    return success_response(data=chat_view(task), request=request)
