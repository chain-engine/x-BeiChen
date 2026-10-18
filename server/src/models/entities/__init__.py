"""ORM 实体子包（北辰 x-BeiChen）。

当前骨架实体：
    AgentTask         任务表（编排中枢的任务载体）
    AgentEvent        事件表（协作事件留痕）
    Customer          客户表（客户管理 Agent）
    CustomerFollowup  客户跟进记录表（状态迁移/跟进留痕）
    CustomerReport    客户报表表（自动出报表产物）
"""

from src.models.entities.agent_event import AgentEvent
from src.models.entities.agent_task import AgentTask
from src.models.entities.customer import Customer
from src.models.entities.customer_followup import CustomerFollowup
from src.models.entities.customer_report import CustomerReport

__all__ = ["AgentTask", "AgentEvent", "Customer", "CustomerFollowup", "CustomerReport"]
