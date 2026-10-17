#!/usr/bin/env python3
"""客户报表业务服务（北辰 x-BeiChen，客户管理 + 任务调度 Agent）。

自动出报表（铁律：确定性模板聚合，不做 LLM 自由生成）：
    - generate_report：聚合客户快照 + 投放统计 → policy 模板 → 落库 customer_reports
    - 洞察总结（"为什么消耗掉了"）二期交给 insight Agent，此处只出数据段
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from src.agents.customer.policy import build_full_report_sections, build_report_sections
from src.core.logger import logger
from src.models.entities.customer_report import CustomerReport
from src.repositories.customer_report_repository import CustomerReportRepository
from src.repositories.customer_repository import CustomerRepository
from src.services.customer_service import to_customer_snapshot


class ReportService:
    """报表业务服务：客户报表生成 / 查询。"""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._report_repo = CustomerReportRepository(session)
        self._customer_repo = CustomerRepository(session)

    def generate_report(self, report_type: str = "daily", customer_ids: list[str] | None = None, now: datetime | None = None) -> CustomerReport:
        """生成一份客户报表并落库（日报/周报）。

        TODO(业务接入): 投放统计 stats_map 从广告平台聚合（复用 ads.get_campaign_stats），
        当前以空统计占位，报表结构与推送链路先行跑通。
        """
        now = now or datetime.now(UTC)
        customers: list[dict[str, Any]] = []
        if customer_ids:
            for cid in customer_ids:
                c = self._customer_repo.get_by_customer_id(cid)
                if c is not None:
                    customers.append(to_customer_snapshot(c))
        else:
            for c in self._customer_repo.list_all(limit=200):
                customers.append(to_customer_snapshot(c))

        if customer_ids and len(customers) == 1:
            content = build_report_sections(customers[0], stats={})
        else:
            content = build_full_report_sections(customers, stats_map={})

        period_start = now - timedelta(days=1 if report_type == "daily" else 7)
        report = CustomerReport(
            report_type=report_type,
            customer_id=customer_ids[0] if customer_ids and len(customer_ids) == 1 else None,
            period_start=period_start,
            period_end=now,
            content=content,
            status="generated",
        )
        self._report_repo.add(report)
        self._report_repo.commit()
        logger.info(f"[ReportService] 报表已生成：type={report_type} customers={len(customers)}")
        return report

    def list_reports(self, report_type: str | None = None, customer_id: str | None = None, page: int = 1, page_size: int = 20) -> tuple[list[CustomerReport], int]:
        offset = (page - 1) * page_size
        if report_type:
            items = self._report_repo.list_by_type(report_type, offset=offset, limit=page_size)
            total = self._report_repo.count(CustomerReport.report_type == report_type)
        elif customer_id:
            items = self._report_repo.list_by_customer(customer_id, offset=offset, limit=page_size)
            total = self._report_repo.count(CustomerReport.customer_id == customer_id)
        else:
            items = self._report_repo.list(order_by=self._report_repo.model_class.id.desc(), offset=offset, limit=page_size)
            total = self._report_repo.count()
        return items, total


__all__ = ["ReportService"]
