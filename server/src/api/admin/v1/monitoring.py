#!/usr/bin/env python3
"""数据监控管理接口（北辰 x-BeiChen 管理后台）。

    POST /monitoring/scan    手动触发一轮监控巡检
    GET  /monitoring/alerts  告警事件列表
"""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi.responses import JSONResponse

from src.api.dependencies import get_monitoring_service
from src.api.response import success_response
from src.services.monitoring_service import MonitoringService

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.post("/scan")
async def trigger_scan(
    request: Request,
    account_ids: list[str] | None = Body(default=None, description="待巡检账户列表，缺省用默认账户"),
    service: MonitoringService = Depends(get_monitoring_service),
) -> JSONResponse:
    """手动触发监控巡检：对每个账户提交 monitor 任务。"""
    task_ids = await service.trigger_scan(account_ids=account_ids)
    return success_response(data={"task_ids": task_ids, "count": len(task_ids)}, request=request)


@router.get("/alerts")
async def list_alerts(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: MonitoringService = Depends(get_monitoring_service),
) -> JSONResponse:
    """告警事件列表。"""
    items, total = service.list_alerts(page=page, page_size=page_size)
    return success_response(
        data={
            "items": [
                {"id": ev.id, "event_type": ev.event_type, "payload": ev.payload, "created_at": ev.created_at.isoformat() if ev.created_at else None}
                for ev in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        request=request,
    )
