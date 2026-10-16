# 二期 Agent 系统技术架构设计

> 北辰 x-BeiChen Agent 编排层的设计说明，对应代码：`server/src/agents/`。

## 1. 设计目标

- **多 Agent 可插拔**：新 Agent 通过注册即可接入顶层调度，不改顶层图。
- **业务与编排分离**：节点函数只做"读状态 → 调策略 → 返回结果"，业务规则外置。
- **断点续跑**：人工接管场景（投诉/退款）通过 interrupt/resume 实现，会话状态持久化。
- **资金铁律**：涉及资金的写操作 Agent 不直接执行，只生成审批单，由审批闸门落地。
- **可观测**：每次任务产生结构化事件，落库 + 事件总线双写。

## 2. 分层结构

```
agents/
├── base.py            # BaseAgent 抽象基类（agent_type/name/description/build()）
├── orchestrator.py    # 顶层调度图：route → subgraph → aggregate
├── registry.py        # AgentRegistry：task_type → AgentSpec（含 BaseAgent 实例）
├── runtime.py         # AgentRuntime：图编译、checkpointer、invoke/resume
├── state.py           # AgentTaskState（共享基类）+ OrchestratorState
├── events.py          # build_event() 事件构造收口
├── approval.py        # 资金审批策略（MONEY_RELATED_ACTIONS / build_money_suggestion）
├── monitor/           # 数据监控子图
│   ├── agent.py       # MonitorAgent(BaseAgent)
│   ├── graph.py       # build_monitor_graph()
│   ├── nodes.py       # pull / calc / judge / alert
│   ├── policy.py      # BUDGET_USAGE_ALERT_THRESHOLD 等业务规则
│   └── state.py       # MonitorState(AgentTaskState)
├── business_chat/     # 商务对话子图
│   ├── agent.py       # BusinessChatAgent(BaseAgent)
│   ├── graph.py       # build_business_chat_graph(llm_provider=None)
│   ├── nodes.py       # classify_intent / retrieve / generate_factory / transfer
│   ├── policy.py      # HUMAN_REQUIRED_KEYWORDS / classify_intent()
│   └── state.py       # ChatState(AgentTaskState)
└── tools/             # 工具注册中心
    ├── registry.py    # ToolRegistry + 三级权限（READ_ONLY / INTERACTIVE / APPROVAL_WRITE）
    ├── ads.py         # 广告投放工具
    ├── rag.py         # 知识库检索
    └── notification.py # 告警通知
```

## 3. 顶层调度图

```
START → route（按 task_type 查 registry）
       → subgraph（嵌入对应业务子图）
       → aggregate（聚合 final_state）
       → END
```

- `route` 节点根据 `state["task_type"]` 从 `AgentRegistry` 查到 `target_agent`。
- 子图通过 `graph.add_node(...)` 嵌入顶层图，LangGraph 自动做同名键合并。
- `aggregate` 节点把 `status/result/error/events/approval_no` 归一化为最终状态。

## 4. 状态设计（TypedDict 继承）

```python
class AgentTaskState(TypedDict, total=False):
    task_id: int
    task_type: str
    payload: dict
    status: str
    result: dict | None
    error: str | None
    events: list[dict]
    approval_no: str | None

class OrchestratorState(AgentTaskState):
    target_agent: str | None

class MonitorState(AgentTaskState):
    raw: dict | None
    metric: dict | None
    anomaly: bool
    suggestion: dict | None

class ChatState(AgentTaskState):
    customer_id: str | None
    message: str | None
    intent: str | None
    knowledge: list[dict] | None
    reply: str | None
    need_human: bool
```

子图只声明私有字段，共享字段通过继承获得，避免四处重复声明。

## 5. 业务子图

### 5.1 monitor（数据监控）

```
START → pull（拉取投放数据，只读工具）
      → calc（计算 CPC / CVR / budget_usage_rate）
      → judge（阈值判定，写 anomaly + suggestion + status=success）
      ├── normal → END
      └── alert  → alert（发告警 + 双事件 + 建议）→ END
```

- 阈值 `BUDGET_USAGE_ALERT_THRESHOLD = 60.0` 在 `monitor/policy.py`。
- 涉及资金的建议通过 `build_money_suggestion()` 构造，标记 `involves_money=True`。
- 事件通过 `build_event(EventType.ALERT_RAISED, "monitor", payload=...)` 统一构造。

### 5.2 business_chat（商务对话）

```
START → intent（classify_intent 规则法）
      → retrieve（RAG 检索，只读工具）
      → generate（LLM 生成）
      ├── consult_policy → END
      └── human_required → interrupt() 暂停 → 人工 resume 后 → END
```

- LLM provider 通过 `generate_node_factory(llm_provider)` 闭包注入，节点本身不 `from src.infras.llm import ...`。
- 提示词在 `server/src/templates/prompts/*.yaml`，通过 `render_messages(key, **vars)` 加载。
- 意图关键词在 `business_chat/policy.py`，调整文案不改节点。

## 6. 断点续跑（interrupt / resume）

- 节点内调用 `langgraph.types.interrupt(payload)` 暂停执行，状态写入 checkpointer。
- `AgentRuntime.resume_task(thread_id, resume_payload)` 从断点恢复，把 `resume_payload` 作为 `interrupt()` 的返回值。
- 任务状态在暂停时写为 `waiting_human`，恢复成功后写为 `success`。

## 7. 工具权限模型

| 级别 | 含义 | 调用方 |
| --- | --- | --- |
| `READ_ONLY` | 查询/检索，Agent 直接调 | pull_data / retrieve / get_campaign_stats |
| `INTERACTIVE` | 需要人工确认 | 预留 |
| `APPROVAL_WRITE` | 涉及资金/写操作，走审批闸门 | adjust_budget / pause_campaign（骨架未直连） |

`tool_registry.invoke(name, level, **kwargs)` 会校验调用级别，未授权直接抛错。

## 8. 事件与审计

- 每条事件结构：`{type, source, target, payload}`，由 `build_event()` 构造。
- 事件类型在 `constants.EventType`：`TASK_CREATED / ALERT_RAISED / SUGGESTION_CREATED / INTENT_DETECTED / TASK_COMPLETED` 等。
- 服务层 `_persist_and_publish_events()` 把事件同时写 `agent_events` 表和发布到事件总线。

## 9. 扩展新 Agent

1. 在 `agents/` 下新建子目录，写 `state.py / nodes.py / graph.py / agent.py`。
2. `agent.py` 里 `class XxxAgent(BaseAgent)`，实现 `build() -> CompiledStateGraph`。
3. 在启动处（或 registry 初始化）把新 Agent 实例注册：`agent_registry.register(XxxAgent())`。
4. 在 `constants.AgentType` 加对应枚举。

顶层图、runtime、事件、审批闸门全部不用动。
