"""客户管理 Agent 子图包（北辰 x-BeiChen，演示实现）。

范式对齐 monitor / business_chat：
    agent.py   对象门面（AgentType.CUSTOMER 注册用）
    state.py   子图状态（继承 AgentTaskState + 客户域字段）
    nodes.py   节点函数（fetch → evaluate → compose → dispatch，演示）
    graph.py   子图构建（编译后注册到顶层编排图）
    policy.py  跟进/报表策略（确定性规则集中点，业务接入时由节点复用）

任务调度保留：周期触发由 APScheduler 外部 job 经 AgentTaskService.submit_task 提交。
"""

from src.agents.customer.agent import CustomerAgent
from src.agents.customer.graph import build_customer_graph
from src.agents.customer.state import CustomerState

__all__ = ["CustomerAgent", "build_customer_graph", "CustomerState"]
