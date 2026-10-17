#!/usr/bin/env python3
"""客户仓储（数据访问层，无业务逻辑）。

状态机迁移规则由 services 层控制（policy.py），仓储只提供查询条件组合。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc

from src.models.entities.customer import Customer
from src.repositories.base_repository import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    """Customer 表数据访问。"""

    model_class = Customer

    # ----------------------------------------------------------
    # 客户管理常用查询
    # ----------------------------------------------------------

    def get_by_customer_id(self, customer_id: str) -> Customer | None:
        """按业务客户编号查询。"""
        return self.first(Customer.customer_id == customer_id)

    def list_by_status(self, status: str, offset: int = 0, limit: int = 20) -> list[Customer]:
        """按客户状态分页查询。"""
        return self.list(
            Customer.status == status,
            order_by=desc(Customer.id),
            offset=offset,
            limit=limit,
        )

    def list_due_followup(self, now: datetime, limit: int = 100) -> list[Customer]:
        """查询跟进到期的客户（next_followup_at < now），调度巡检用。"""
        return self.list(
            Customer.next_followup_at.is_not(None),
            Customer.next_followup_at < now,
            order_by=Customer.next_followup_at.asc(),
            limit=limit,
        )

    def list_all(self, offset: int = 0, limit: int = 100) -> list[Customer]:
        """全量客户（报表聚合 / 巡检兜底）。"""
        return self.list(order_by=desc(Customer.id), offset=offset, limit=limit)
