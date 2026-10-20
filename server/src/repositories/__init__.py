"""仓储层（数据访问层）包（北辰 x-BeiChen）。

- base_repository:           通用 CRUD 基类（BaseRepository）
- agent_task_repository:     Agent 任务表访问
- agent_event_repository:    协作事件表访问

扩展约定：新增业务域时照抄风格新增 XxxRepository(BaseRepository[XxxModel])。
"""

from src.repositories.agent_event_repository import AgentEventRepository
from src.repositories.agent_task_repository import AgentTaskRepository
from src.repositories.base_repository import BaseRepository

__all__ = [
    "BaseRepository",
    "AgentTaskRepository",
    "AgentEventRepository",
]
