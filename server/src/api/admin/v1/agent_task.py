#!/usr/bin/env python3
"""Agent 编排管理接口（北辰 x-BeiChen 管理后台）。

    GET    /agents            Agent 注册表列表
    POST   /tasks             提交 Agent 任务
    GET    /tasks             任务列表（可按状态/类型过滤）
    GET    /tasks/{task_id}   任务详情
    POST   /tasks/{task_id}/resume  人工接管恢复（interrupt/resume）
    GET    /events            协作事件列表
    GET    /events/{event_id} 协作事件详情

数据流向：api 层（本文件）→ services（AgentTaskService）→ repositories/agents。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from src.api.dependencies import get_task_service
from src.api.response import success_response
from src.agents.registry import agent_registry
from src.schemas.agent import AgentTaskCreate, AgentTaskResumeIn
from src.services.agent_task_service import AgentTaskService

router = APIRouter(tags=["Agent 任务管理"])


@router.get("/agents", summary="Agent 注册表列表")
async def list_agents(request: Request) -> JSONResponse:
    """Agent 注册表列表（无需数据库）。"""
    specs = agent_registry.list_specs()
    return success_response(
        data={
            "items": [
                {
                    "type": str(spec.agent_type),
                    "name": spec.name,
                    "description": spec.description,
                    "enabled": spec.enabled,
                }
                for spec in specs
            ],
            "total": len(specs),
        },
        request=request,
    )


@router.post("/tasks", summary="提交 Agent 任务")
async def submit_task(
    body: AgentTaskCreate,
    request: Request,
    service: AgentTaskService = Depends(get_task_service),
) -> JSONResponse:
    """提交一个 Agent 任务（同步执行）。"""
    task = await service.submit_task(
        task_type=str(body.task_type),
        payload=body.payload,
        timeout_at=body.timeout_at,
    )
    return success_response(data=_task_to_dict(task), request=request)


@router.get("/tasks", summary="任务列表")
async def list_tasks(
    request: Request,
    status: str | None = Query(default=None, description="按任务状态过滤（TaskStatus）"),
    task_type: str | None = Query(default=None, description="按任务类型过滤（AgentType）"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: AgentTaskService = Depends(get_task_service),
) -> JSONResponse:
    """任务列表（管理后台任务面板）。"""
    items, total = service.list_tasks(status=status, task_type=task_type, page=page, page_size=page_size)
    return success_response(
        data={"items": [_task_to_dict(t) for t in items], "total": total, "page": page, "page_size": page_size},
        request=request,
    )


@router.get("/tasks/{task_id}", summary="任务详情")
async def get_task(
    task_id: int,
    request: Request,
    service: AgentTaskService = Depends(get_task_service),
) -> JSONResponse:
    """任务详情。"""
    task = service.get_task(task_id)
    return success_response(data=_task_to_dict(task), request=request)


@router.post("/tasks/{task_id}/resume", summary="恢复人工接管任务")
async def resume_task(
    task_id: int,
    body: AgentTaskResumeIn,
    request: Request,
    service: AgentTaskService = Depends(get_task_service),
) -> JSONResponse:
    """人工接管：恢复被 interrupt 暂停的任务。"""
    task = await service.resume_task(
        task_id=task_id,
        decision=body.decision,
        remark=body.remark,
        extra=body.extra,
    )
    return success_response(data=_task_to_dict(task), request=request)


@router.get("/events", summary="协作事件列表")
async def list_events(
    request: Request,
    event_type: str | None = Query(default=None, description="按事件类型过滤（EventType）"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: AgentTaskService = Depends(get_task_service),
) -> JSONResponse:
    """协作事件列表（管理后台事件面板 / 审计）。"""
    items, total = service.list_events(event_type=event_type, page=page, page_size=page_size)
    return success_response(
        data={
            "items": [_event_to_dict(ev) for ev in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        request=request,
    )


@router.get("/events/{event_id}", summary="协作事件详情")
async def get_event(
    event_id: int,
    request: Request,
    service: AgentTaskService = Depends(get_task_service),
) -> JSONResponse:
    """单条协作事件详情（含完整 payload，审计面板查看）。"""
    event = service.get_event(event_id)
    return success_response(data=_event_to_dict(event), request=request)


def _event_to_dict(ev) -> dict:
    """协作事件实体 → 响应字典（列表 / 详情复用）。"""
    return {
        "id": ev.id,
        "event_type": ev.event_type,
        "source_agent": ev.source_agent,
        "target_agent": ev.target_agent,
        "payload": ev.payload,
        "status": ev.status,
        "created_at": ev.created_at.isoformat() if ev.created_at else None,
    }


def _task_to_dict(task) -> dict:
    """任务实体 → 响应字典（骨架统一转换点，后续可用 Pydantic schema 替换）。"""
    return {
        "id": task.id,
        "task_type": task.task_type,
        "payload": task.payload,
        "status": task.status,
        "assignee_agent": task.assignee_agent,
        "thread_id": task.thread_id,
        "retry_count": task.retry_count,
        "max_retries": task.max_retries,
        "error_message": task.error_message,
        "approval_no": task.approval_no,
        "result": task.result,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }
