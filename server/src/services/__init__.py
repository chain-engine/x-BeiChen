"""业务服务层（北辰 x-BeiChen）。

职责：业务规则 / 事务编排 / 跨仓储协作；禁读 Request；依赖 repositories + agents 编排层。

- agent_task_service:    Agent 任务管理（提交/恢复/查询/事件查询）

扩展约定：新增业务域（人社政策问答 / 智能客服 / 材料核验等）照此风格新增 Service。
"""

from src.services.agent_task_service import AgentTaskService

__all__ = ["AgentTaskService"]
