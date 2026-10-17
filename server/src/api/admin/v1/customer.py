#!/usr/bin/env python3
"""客户管理 + 任务调度 Agent 对外接口（北辰 x-BeiChen 管理后台）。

功能性 Agent 主线（对齐客户原始需求：跟进客户状态 / 定时任务 / 自动出报表）：

    POST   /customers/run                       提交 customer 子图任务（跟进巡检/指定客户/全量/报表）
    POST   /customers/reports/trigger          手动触发客户报表（ReportService，不经子图）
    GET    /customers/reports                  报表列表
    GET    /customers/{customer_id}/followups  跟进任务列表（Agent 产出，可审计）

客户数据管理（CRUD / 状态迁移）不在本 Agent 职责内，属二期独立 CRM 模块。
数据流向：api 层（本文件）→ services（AgentTaskService / CustomerService / ReportService）→ repositories。
"""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi.responses import JSONResponse

from src.api.dependencies import get_customer_service, get_report_service, get_task_service
from src.api.response import success_response
from src.constants import AgentType
from src.core.exceptions import ValidationException
from src.schemas.customer import CustomerTaskIn, ReportTriggerIn, customer_view, followup_to_dict, report_to_dict
from src.services.agent_task_service import AgentTaskService
from src.services.customer_service import CustomerService
from src.services.report_service import ReportService

router = APIRouter(prefix="/customers", tags=["客户管理 + 任务调度 Agent"])


# ── Agent 任务提交（静态路由先声明，避免被 /{customer_id} 抢先匹配）────────


@router.post("/run", summary="提交客户管理+任务调度 Agent 任务")
async def run_customer_agent(
    request: Request,
    body: CustomerTaskIn = Body(default=...),
    service: AgentTaskService = Depends(get_task_service),
) -> JSONResponse:
    """提交一轮 customer 子图任务：跟进到期巡检（默认）/ 指定客户 / 全量 / 报表任务。"""
    if body.scope == "by_ids" and not body.customer_ids:
        raise ValidationException("scope=by_ids 时 customer_ids 必填")
    task = await service.submit_task(
        task_type=AgentType.CUSTOMER.mark,
        payload={"scope": body.scope, "customer_ids": body.customer_ids},
    )
    return success_response(data=customer_view(task), request=request)


# ── 报表（静态路由先声明，避免被 /{customer_id} 抢先匹配）────────


@router.post("/reports/trigger", summary="手动触发客户报表")
async def trigger_report(
    request: Request,
    body: ReportTriggerIn = Body(default=...),
    service: ReportService = Depends(get_report_service),
) -> JSONResponse:
    """手动触发一份客户报表（确定性模板聚合，自动出报表）。"""
    report = service.generate_report(report_type=body.report_type, customer_ids=body.customer_ids)
    return success_response(data=report_to_dict(report), request=request)


@router.get("/reports", summary="报表列表")
async def list_reports(
    request: Request,
    report_type: str | None = Query(default=None, description="按报表类型过滤（daily/weekly）"),
    customer_id: str | None = Query(default=None, description="按客户编号过滤"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: ReportService = Depends(get_report_service),
) -> JSONResponse:
    """报表列表（管理后台报表面板）。"""
    items, total = service.list_reports(report_type=report_type, customer_id=customer_id, page=page, page_size=page_size)
    return success_response(
        data={"items": [report_to_dict(r) for r in items], "total": total, "page": page, "page_size": page_size},
        request=request,
    )


# ── 跟进任务（Agent 产出物查询）──────────────────────────


@router.get("/{customer_id}/followups", summary="跟进任务列表")
async def list_followups(
    customer_id: str,
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: CustomerService = Depends(get_customer_service),
) -> JSONResponse:
    """跟进任务列表（客户管理 + 任务调度 Agent 产出的跟进记录，可审计）。"""
    items, total = service.list_followups(customer_id, page=page, page_size=page_size)
    return success_response(
        data={"items": [followup_to_dict(f) for f in items], "total": total, "page": page, "page_size": page_size},
        request=request,
    )
