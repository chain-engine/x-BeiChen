"""Agent 编排层（北辰 x-BeiChen，LangGraph + LangChain 标准实现）。

目录职责：
    state.py        共享状态 TypedDict（顶层编排 + 子图合并契约）
    base.py         BaseAgent 抽象基类（子图构建契约）
    registry.py     Agent 注册表（映射表路由："派给谁"）
    runtime.py      AgentRuntime（编排图构建/checkpointer/invoke/resume）
    orchestrator.py 顶层调度中枢编排图（节点+条件边："怎么干"）
    tools/          工具注册中心（三级权限：只读/审批写/执行写）
    monitor/        数据监控 Agent（子图）
    business_chat/  商务对话 Agent（子图）
二期占位：customer / content / customer_service / insight（注册即可扩展）
"""

from src.agents.base import BaseAgent
from src.agents.registry import AgentRegistry, AgentSpec, agent_registry
from src.agents.runtime import AgentRuntime, get_agent_runtime
from src.agents.state import AgentTaskState, OrchestratorState

__all__ = [
    "BaseAgent",
    "AgentRegistry",
    "AgentSpec",
    "agent_registry",
    "AgentRuntime",
    "get_agent_runtime",
    "OrchestratorState",
    "AgentTaskState",
]
