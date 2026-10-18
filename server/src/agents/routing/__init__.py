"""路由决策子包（北辰 x-BeiChen）。

把"派给谁"的决策从编排节点抽离为独立组件 RouteResolver：
显式查表 / LLM 动态选择 / hybrid（显式优先、LLM 兜底）三种模式。
"""

from src.agents.routing.resolver import RouteDecision, RouteResolver

__all__ = ["RouteDecision", "RouteResolver"]
