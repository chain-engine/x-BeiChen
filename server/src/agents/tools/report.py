#!/usr/bin/env python3
"""客户报表渲染工具（北辰 x-BeiChen，客户管理 Agent）。

确定性模板渲染（铁律：报表可复算、可审计）：
    - 输入为 policy.build_report_sections / build_full_report_sections 的聚合结果
    - 输出为可直接推送的文本（纯函数，无副作用）
洞察总结（"为什么消耗掉了"）二期由 insight Agent 补充，此处不做 LLM 生成。
当前 Agent 为演示实现（dispatch 节点不调用本工具），本工具保留供业务接入复用。
"""

from __future__ import annotations

from typing import Any

from src.agents.tools.registry import ToolSpec, tool_registry
from src.constants import ToolPermissionLevel
from src.core.logger import logger


def render_report(sections: dict[str, Any], title: str = "客户报表") -> str:
    """渲染报表为文本（只读纯函数，模板化）。

    Args:
        sections: policy.build_report_sections / build_full_report_sections 的返回
        title: 报表标题（如"日报/周报"）
    """
    logger.info(f"[Report] render_report title={title}")
    rows = sections.get("rows")
    if rows is not None:
        # 全量客户报表
        lines = [
            f"{title}（共 {sections.get('total_customers', 0)} 客户）",
            f"活跃 {sections.get('active_customers', 0)} / 沉睡 {sections.get('dormant_customers', 0)}，合同总额 {sections.get('total_contract_amount', 0)}",
            "-" * 40,
        ]
        for r in rows:
            lines.append(
                f"  {r.get('customer_name', '')}({r.get('customer_id', '')}) "
                f"[{r.get('status', '')}] 消耗 {r.get('period_cost', 0)} / 转化 {r.get('period_conversions', 0)}"
            )
    else:
        # 单客户报表
        lines = [
            f"{title}：{sections.get('customer_name', '')}（{sections.get('customer_id', '')}）",
            f"  状态 {sections.get('status', '')} / 合同 {sections.get('contract_amount', 0)} / 预算 {sections.get('budget', 0)}",
            f"  区间消耗 {sections.get('period_cost', 0)} / 转化 {sections.get('period_conversions', 0)}",
        ]
    lines.append(sections.get("summary", ""))
    return "\n".join(lines)


def register_report_tools() -> None:
    """注册报表渲染工具（幂等）。"""
    if tool_registry.get("report.render_report") is None:
        tool_registry.register(ToolSpec(name="report.render_report", description="渲染客户报表文本（只读，确定性模板）", func=render_report, permission_level=ToolPermissionLevel.READ_ONLY))


register_report_tools()

__all__ = ["render_report", "register_report_tools"]
