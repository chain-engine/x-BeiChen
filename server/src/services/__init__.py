"""业务服务层（北辰 x-BeiChen）。

职责：业务规则 / 事务编排 / 跨仓储协作；禁读 Request；依赖 repositories + agents 编排层。

- agent_task_service:    Agent 任务管理（提交/恢复/查询/事件查询）
- monitoring_service:    数据监控业务（巡检触发/告警查询）
- customer_service:      客户业务（快照/状态迁移/跟进记录，确定性写）
- report_service:        客户报表业务（确定性模板聚合）

扩展约定：新增业务域（内容创作/客服转化/投放洞察）照此风格新增 Service。
"""

from src.services.agent_task_service import AgentTaskService
from src.services.customer_service import CustomerService
from src.services.monitoring_service import MonitoringService
from src.services.report_service import ReportService

__all__ = ["AgentTaskService", "MonitoringService", "CustomerService", "ReportService"]
