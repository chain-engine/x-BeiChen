#!/usr/bin/env python3
"""客户跟进记录仓储（数据访问层，无业务逻辑）。"""

from __future__ import annotations

from sqlalchemy import desc

from src.models.entities.customer_followup import CustomerFollowup
from src.repositories.base_repository import BaseRepository


class CustomerFollowupRepository(BaseRepository[CustomerFollowup]):
    """CustomerFollowup 表数据访问。"""

    model_class = CustomerFollowup

    def list_by_customer(self, customer_id: str, offset: int = 0, limit: int = 20) -> list[CustomerFollowup]:
        """按客户编号分页查询跟进记录（倒序，最新在前）。"""
        return self.list(
            CustomerFollowup.customer_id == customer_id,
            order_by=desc(CustomerFollowup.id),
            offset=offset,
            limit=limit,
        )
