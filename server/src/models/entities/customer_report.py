#!/usr/bin/env python3
"""客户报表表 ORM 实体。

自动出报表产物留痕：
    - report_type：daily 日报 / weekly 周报
    - customer_id 为空表示全量客户报表，非空表示单客户报表
    - content 为报表 JSON（确定性模板聚合，不做 LLM 自由生成）
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infras.database import Base


class CustomerReport(Base):
    """客户报表产物（对应 customer_reports 表）。"""

    __tablename__ = "customer_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键")
    report_type: Mapped[str] = mapped_column(String(20), index=True, nullable=False, comment="报表类型（daily/weekly）")
    customer_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True, comment="客户编号（空=全量客户报表）")
    period_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="统计区间起点")
    period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="统计区间终点")
    content: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="报表数据（确定性聚合结果）")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="generated", comment="报表状态（generated/sent）")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CustomerReport id={self.id} type={self.report_type} cid={self.customer_id}>"
