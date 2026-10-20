"""Agent 工具包（北辰 x-BeiChen）。

- registry:    工具注册中心（ToolRegistry + 权限校验：read / write）

已随项目定位调整移除的工具：广告平台（ads）、客户管理（crm）、
通知（notification）、RAG 检索（rag）、报表渲染（report）。

新增业务工具：新建模块并按 registry 风格注册（ToolSpec + ToolRegistry），
照 tools/registry.py 的权限模型（read 只读可直调 / write 写由人工执行）约束。
"""

from src.agents.tools.registry import ToolRegistry, ToolSpec, tool_registry

__all__ = [
    "ToolRegistry",
    "ToolSpec",
    "tool_registry",
]
