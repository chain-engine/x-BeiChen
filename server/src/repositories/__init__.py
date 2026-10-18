"""仓储层（数据访问层）包（北辰 x-BeiChen）。

- base_repository:           通用 CRUD 基类（BaseRepository）
- agent_task_repository:     Agent 任务表访问
- agent_event_repository:    协作事件表访问
- customer_repository:       客户表访问（客户管理 Agent）
- customer_followup_repository:客户跟进记录表访问
- customer_report_repository:客户报表表访问

扩展约定：新增业务域时照抄风格新增 XxxRepository(BaseRepository[XxxModel])。
"""

from src.repositories.agent_event_repository import AgentEventRepository
from src.repositories.agent_task_repository import AgentTaskRepository
from src.repositories.base_repository import BaseRepository
from src.repositories.customer_followup_repository import CustomerFollowupRepository
from src.repositories.customer_report_repository import CustomerReportRepository
from src.repositories.customer_repository import CustomerRepository

__all__ = [
    "BaseRepository",
    "AgentTaskRepository",
    "AgentEventRepository",
    "CustomerRepository",
    "CustomerFollowupRepository",
    "CustomerReportRepository",
]
