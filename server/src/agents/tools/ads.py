#!/usr/bin/env python3
"""广告平台工具包（北辰 x-BeiChen）。

封装海外广告平台（Google Ads 等）的操作能力。骨架阶段全部为 mock / todo：
    - 只读查询（get_campaign_stats）：直接返回构造数据
    - 写操作（adjust_budget / pause_campaign）：审批写，仅生成审批单号（approval_no），
      由广告审批通过后的执行器真正调用平台 API（资金操作必须留痕、不可抵赖）

对接真实平台时：在函数体内替换为广告平台 API 调用，保持函数签名与权限级别不变。
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from src.agents.tools.registry import ToolSpec, tool_registry
from src.constants import ToolPermissionLevel
from src.core.logger import logger


def get_campaign_stats(account_id: str, campaign_id: str | None = None) -> dict[str, Any]:
    """查询广告投放数据（只读）。

    TODO(业务接入): 调用广告平台报表 API / 本地同步库拉取真实数据。
    当前返回 mock 数据，供监控 Agent 的判定节点跑通链路。
    """
    logger.info(f"[Ads] get_campaign_stats account={account_id} campaign={campaign_id}")
    return {
        "account_id": account_id,
        "campaign_id": campaign_id or "camp_001",
        "cost": 5200.00,          # 今日消耗（元）
        "conversions": 12,        # 今日转化数
        "impressions": 32000,     # 曝光
        "clicks": 860,            # 点击
        "budget": 8000.00,        # 日预算
        "currency": "CNY",
        "fetched_at": datetime.now(UTC).isoformat(),
    }


def adjust_budget(campaign_id: str, new_budget: float, reason: str = "") -> dict[str, Any]:
    """调整广告预算（审批写：仅创建审批单，不直接执行）。

    资金类操作铁律：Agent 不直接调用平台写接口；
    此函数只生成审批单号，由审批通过后的执行器（exec_write 工具）真正执行。
    """
    approval_no = f"APV{datetime.now(UTC):%Y%m%d}{uuid4().hex[:8].upper()}"
    logger.warning(f"[Ads] adjust_budget 生成审批单 {approval_no}：campaign={campaign_id} budget={new_budget}")
    return {
        "action": "adjust_budget",
        "campaign_id": campaign_id,
        "new_budget": new_budget,
        "reason": reason,
        "approval_no": approval_no,   # 审批凭证：留痕、不可抵赖
        "executed": False,            # 尚未执行，等待审批
    }


def pause_campaign(campaign_id: str, reason: str = "") -> dict[str, Any]:
    """暂停广告计划（审批写：仅创建审批单，不直接执行）。"""
    approval_no = f"APV{datetime.now(UTC):%Y%m%d}{uuid4().hex[:8].upper()}"
    logger.warning(f"[Ads] pause_campaign 生成审批单 {approval_no}：campaign={campaign_id}")
    return {
        "action": "pause_campaign",
        "campaign_id": campaign_id,
        "reason": reason,
        "approval_no": approval_no,
        "executed": False,
    }


def register_ads_tools() -> None:
    """注册广告工具到工具注册中心（幂等）。"""
    if tool_registry.get("ads.get_campaign_stats") is None:
        tool_registry.register(ToolSpec(name="ads.get_campaign_stats", description="查询广告投放数据（只读）", func=get_campaign_stats, permission_level=ToolPermissionLevel.READ_ONLY))
        tool_registry.register(ToolSpec(name="ads.adjust_budget", description="调整广告预算（审批写）", func=adjust_budget, permission_level=ToolPermissionLevel.APPROVAL_WRITE))
        tool_registry.register(ToolSpec(name="ads.pause_campaign", description="暂停广告计划（审批写）", func=pause_campaign, permission_level=ToolPermissionLevel.APPROVAL_WRITE))


register_ads_tools()

__all__ = ["get_campaign_stats", "adjust_budget", "pause_campaign", "register_ads_tools"]
