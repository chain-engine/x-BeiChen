#!/usr/bin/env python3
"""客户实体表 ORM 实体。

客户管理 + 任务调度 Agent（customer）的核心数据载体：
    - 客户状态机（lead → negotiating → signed → active → dormant → churned）
    - 跟进节奏（next_followup_at / last_followup_at）
    - 合同与预算（资金相关字段，写操作走审批闸门）

状态迁移规则集中在 agents/customer/policy.py，由 services 层确定性执行。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infras.database import Base


class Customer(Base):
    """客户实体（对应 customers 表）。"""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键")
    customer_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False, comment="业务客户编号（如 cust_001）")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="客户名称")
    industry: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="所属行业")
    status: Mapped[str] = mapped_column(String(20), index=True, nullable=False, default="lead", comment="客户状态（CustomerStatus）")
    contract_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True, comment="合同金额")
    budget: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True, comment="月度投放预算")
    next_followup_at: Mapped[datetime | None] = mapped_column(DateTime, index=True, nullable=True, comment="下次跟进时间（调度依据）")
    last_followup_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="最近跟进时间")
    assignee: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="负责销售/运营")
    remark: Mapped[str | None] = mapped_column(Text, nullable=True, comment="备注")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Customer id={self.id} cid={self.customer_id} status={self.status}>"
