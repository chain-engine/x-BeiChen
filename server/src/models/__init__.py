"""数据模型包（北辰 x-BeiChen）。

- entities/：SQLAlchemy ORM 实体（自动建表：新实体在此导出后，启动时 init_database 自动补齐缺失表）
- 聚合/领域模型（按需扩展）
"""

from src.models.entities import AgentEvent, AgentTask

__all__ = ["AgentTask", "AgentEvent"]
