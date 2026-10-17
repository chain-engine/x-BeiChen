#!/usr/bin/env python3
"""客户报表仓储（数据访问层，无业务逻辑）。"""

from __future__ import annotations

from sqlalchemy import desc

from src.models.entities.customer_report import CustomerReport
from src.repositories.base_repository import BaseRepository


class CustomerReportRepository(BaseRepository[CustomerReport]):
    """CustomerReport 表数据访问。"""

    model_class = CustomerReport

    def list_by_type(self, report_type: str, offset: int = 0, limit: int = 20) -> list[CustomerReport]:
        """按报表类型分页查询（daily/weekly）。"""
        return self.list(
            CustomerReport.report_type == report_type,
            order_by=desc(CustomerReport.id),
            offset=offset,
            limit=limit,
        )

    def list_by_customer(self, customer_id: str, offset: int = 0, limit: int = 20) -> list[CustomerReport]:
        """按客户编号查询历史报表。"""
        return self.list(
            CustomerReport.customer_id == customer_id,
            order_by=desc(CustomerReport.id),
            offset=offset,
            limit=limit,
        )
