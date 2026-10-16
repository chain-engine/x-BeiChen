# 任务型 Agent 实操教程

> 基于 LangGraph 构建任务型 Agent 的实战指南，所有示例取自北辰 x-BeiChen 实际代码。

## 1. 核心概念

LangGraph 把 Agent 抽象成一张**状态图（StateGraph）**：

- **State**：在图中流动的数据载体（TypedDict）。
- **Node**：一个函数 `(state) -> partial_state`，做一步业务动作。
- **Edge**：节点之间的连接，分普通边和条件边。
- **Interrupt**：在节点内暂停，等外部输入恢复。

## 2. 定义状态

```python
# server/src/agents/state.py
from typing import TypedDict, Any

class AgentTaskState(TypedDict, total=False):
    task_id: int
    status: str
    result: dict | None
    events: list[dict]

class MonitorState(AgentTaskState):
    raw: dict | None
    metric: dict | None
    anomaly: bool
```

要点：
- 用 `total=False` 让字段全部可选，节点返回的 dict 只包含要更新的字段。
- 子图状态继承共享基类，避免重复声明。

## 3. 写节点

节点签名固定 `(state) -> dict`，返回值是要更新的状态片段：

```python
def judge_node(state: MonitorState) -> dict:
    metric = state.get("metric") or {}
    usage = metric.get("budget_usage_rate", 0)
    anomaly = usage > 60.0
    return {"anomaly": anomaly, "status": "success"}
```

节点不抛"业务异常"来表达分支，而是返回标志位（`anomaly: bool`），由条件边决定下一步。

## 4. 组装图

```python
from langgraph.graph import StateGraph, START, END

def build_monitor_graph():
    g = StateGraph(MonitorState)
    g.add_node("pull", pull_data_node)
    g.add_node("calc", calc_metric_node)
    g.add_node("judge", judge_node)
    g.add_node("alert", alert_node)

    g.add_edge(START, "pull")
    g.add_edge("pull", "calc")
    g.add_edge("calc", "judge")

    # 条件边：根据 anomaly 走不同分支
    g.add_conditional_edges(
        "judge",
        lambda s: "alert" if s.get("anomaly") else "end",
        {"alert": "alert", "end": END},
    )
    g.add_edge("alert", END)
    return g.compile()
```

## 5. 注入依赖（闭包工厂）

LangGraph 节点签名固定，要传入 LLM client、配置等依赖，用闭包：

```python
def generate_node_factory(llm_provider):
    def generate_node(state: ChatState) -> dict:
        model = llm_provider.get_chat_model()
        ...
        return {"reply": reply}
    return generate_node

# 构建图时注入
graph.add_node("generate", generate_node_factory(llm_provider))
```

好处：节点函数本身不 `from src.infras.llm import ...`，单测时传 mock provider 即可。

## 6. 提示词外置

提示词放在 `templates/prompts/*.yaml`：

```yaml
# business_chat.yaml
chat_reply:
  messages:
    - role: system
      content: 你是广告联盟商务助手。
    - role: human
      content: |
        客户问题：{question}
        知识库：{knowledge}
```

代码里渲染：

```python
from src.templates import render_messages
from langchain_core.messages import HumanMessage, SystemMessage

messages = render_messages("chat_reply", question=q, knowledge=k)
lc_messages = [SystemMessage(content=m["content"]) if m["role"]=="system"
               else HumanMessage(content=m["content"]) for m in messages]
response = model.invoke(lc_messages)
```

> 坑：不要把已经渲染好的字符串再喂给 `ChatPromptTemplate.from_messages()`，否则 `{knowledge}` 里 dict 的花括号会被二次解析成变量。直接构造 `SystemMessage/HumanMessage` 最稳。

## 7. Interrupt 断点续跑

人工接管场景：节点内调 `interrupt(payload)` 暂停：

```python
from langgraph.types import interrupt

if state.get("intent") == "human_required":
    human_input = interrupt({
        "reason": "客户请求人工介入",
        "customer_id": state.get("customer_id"),
        "message": state.get("message"),
    })
    # resume 后 human_input 就是 resume 时传回来的值
    reply = f"已转接人工：{human_input}"
    return {"reply": reply, "status": "success"}
```

恢复：

```python
runtime.resume_task(thread_id, {"decision": "approve", "remark": "已处理"})
```

暂停时 runtime 把任务状态写为 `waiting_human`，事件总线发通知。

## 8. Checkpointer

多轮会话和断点续跑需要 checkpointer（SQLite / Postgres）。北辰骨架用内存 checkpointer，生产换 Postgres：

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
graph.compile(checkpointer=checkpointer)
```

调用时传 `config={"configurable": {"thread_id": task_id}}`，同 thread_id 自动续上会话。

## 9. 子图嵌套顶层图

业务子图可以嵌入顶层调度图：

```python
top = StateGraph(OrchestratorState)
top.add_node("sub_monitor", monitor_graph)
top.add_node("sub_chat", chat_graph)
```

LangGraph 自动做同名键合并：子图返回的 `status/events/result` 会合并到顶层状态。子图私有字段（`raw/metric`）不外泄。

## 10. 常见坑

| 坑 | 解法 |
| --- | --- |
| normal 分支不经过收尾节点，任务状态停在 running | 在判定节点里就写 `status=success`，不依赖 END 兜底 |
| TypedDict 继承时重复传 `total=False` 报错 | 基类设 `total=False`，子类直接 `class Child(Base)` |
| 节点 import 基础设施导致单测没法 mock | 用闭包工厂在 build 时注入 |
| 事件 dict 字段名拼错 | 统一用 `build_event(type, source, payload)` helper |
| 双重模板渲染 | 渲染好的字符串直接喂 Message 对象，不再走 ChatPromptTemplate |
| 资金写操作被 Agent 直接执行 | 在 policy 层标记 `involves_money=True`，节点不调 APPROVAL_WRITE 工具 |

## 11. 自检

每次改完跑：

```bash
cd server
.\.venv\Scripts\python.exe scripts\verify_agent_flow.py
```

三条链路全绿才算完成。
