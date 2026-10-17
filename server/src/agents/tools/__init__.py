"""Agent 工具包（北辰 x-BeiChen）。

- registry:    工具注册中心（ToolRegistry + 三级权限校验）
- ads:         广告平台工具（只读查询 / 审批写操作，mock）
- crm:         客户管理工具（客户快照只读，mock）
- report:      客户报表渲染工具（只读确定性模板）
- rag:         RAG 知识检索工具（政策/FAQ，mock）
- notification:告警通知工具（mock）

二期扩展：email / 竞品情报 等，照同一风格注册。
"""

from src.agents.tools.ads import adjust_budget, get_campaign_stats, pause_campaign
from src.agents.tools.crm import get_customer_snapshot, list_all_customer_snapshots, list_customer_snapshots_by_ids, list_due_followup_snapshots
from src.agents.tools.notification import send_alert
from src.agents.tools.rag import retrieve
from src.agents.tools.report import render_report
from src.agents.tools.registry import ToolRegistry, ToolSpec, tool_registry

__all__ = [
    "ToolRegistry",
    "ToolSpec",
    "tool_registry",
    "get_campaign_stats",
    "adjust_budget",
    "pause_campaign",
    "list_all_customer_snapshots",
    "list_due_followup_snapshots",
    "list_customer_snapshots_by_ids",
    "get_customer_snapshot",
    "render_report",
    "retrieve",
    "send_alert",
]
