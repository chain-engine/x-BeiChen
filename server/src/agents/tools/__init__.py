"""Agent 工具包（北辰 x-BeiChen）。

- registry:    工具注册中心（ToolRegistry + 三级权限校验）

已随项目定位调整移除的工具：广告平台（ads）、客户管理（crm）、
通知（notification）、RAG 检索（rag）、报表渲染（report）。

新增业务工具：新建模块并按 registry 风格注册（ToolSpec + ToolRegistry），
照 tools/registry.py 的权限模型（read / approval_write / exec_write）约束。
"""

from src.agents.tools.registry import ToolRegistry, ToolSpec, tool_registry

__all__ = [
    "ToolRegistry",
    "ToolSpec",
    "tool_registry",
]
