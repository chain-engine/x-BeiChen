# 北辰管理后台落地架构（传统分层修正版）

> 对应代码：`server/src/api/`、`server/src/services/`、`server/src/repositories/`。
> 原则：**单向依赖，上层知道下层，下层不知道上层**。

## 1. 分层与依赖方向

```
api/        ← HTTP 入口：路由、依赖注入、请求/响应校验、异常映射
  ↓
services/   ← 业务编排：调 AgentRuntime、落库、发事件、事务边界
  ↓
repositories/ ← 数据访问：SQLAlchemy 仓储，只暴露 CRUD，不含业务规则
  ↓
models/     ← ORM 实体（agent_tasks / agent_events）
```

反向依赖禁止：
- `repositories` 不能 import `services` 或 `api`。
- `models` 不能 import 任何上层。
- `agents/` 是 services 调用的"业务能力库"，不反向 import api/services。

## 2. 目录与职责

```
src/
├── api/
│   ├── router.py           # 总路由聚合
│   ├── dependencies.py     # FastAPI 依赖：get_db / get_orchestrator_service
│   └── admin/
│       └── v1/
│           ├── tasks.py     # 任务 CRUD / 提交 / 查询
│           ├── agents.py    # Agent 注册表查询
│           └── events.py    # 事件审计查询
├── services/
│   ├── orchestrator_service.py  # AgentOrchestratorService：提交任务 / 查询状态 / resume
│   └── monitor_service.py      # 监控业务（预留）
├── repositories/
│   ├── task_repo.py         # AgentTask 仓储
│   └── event_repo.py        # AgentEvent 仓储
├── models/
│   └── entities/
│       ├── agent_task.py    # agent_tasks 表
│       └── agent_event.py   # agent_events 表
└── schemas/                 # Pydantic 请求/响应模型（DTO）
```

## 3. 请求生命周期

以"提交一个 Agent 任务"为例：

1. **API 层** `POST /admin/v1/tasks`：
   - 用 `TaskCreate` schema 校验入参。
   - 通过依赖注入拿到 `AgentOrchestratorService`。
   - 调 `service.submit(task_type, payload)`。
2. **Service 层**：
   - 在 `agent_tasks` 表插入一条 `status=running` 的记录。
   - 调 `AgentRuntime.invoke_task(task_type, payload, task_id=...)`。
   - runtime 跑图，返回 final_state。
   - `_apply_final_state()` 把 `status/result/error/approval_no` 回写任务记录。
   - `_persist_and_publish_events()` 把事件批量插入 `agent_events` 并发布到事件总线。
3. **Repository 层**：纯 SQLAlchemy `session.execute(...)`，无业务判断。

## 4. 与 Agent 编排层的边界

- Service 层是 AgentRuntime 的**唯一外部调用方**。
- API 层**不直接 import** `agents.runtime` 或 `agents.registry`。
- Agent 节点函数**不直接 import** `repositories` 或 `services`，它们要副作用（发事件、调工具）都通过：
  - `tool_registry.invoke(...)` 调工具；
  - 返回 `events` 字段由 service 统一落库。

这样换存储、换事件总线、加缓存，都不会动到 Agent 节点。

## 5. 横切关注点

| 关注点 | 落点 |
| --- | --- |
| 配置 | `core/config.py`（pydantic-settings，读 `.env`） |
| 日志 | `core/logger.py`（结构化 logger，带 request_id） |
| 异常 | `core/exceptions.py` + 全局 exception_handler |
| 跨域 | `core/middleware.py`（CORS，生产环境按白名单放行） |
| 数据库会话 | `api/dependencies.py` 的 `get_db()`（请求级 session） |
| 定时任务 | `scheduling/`（APScheduler 拉数据、巡检） |

## 6. 为什么不把业务规则下沉到 repository

- Repository 只做"数据存取"，否则换存储（比如换 MySQL 到 PG）要重写业务。
- 业务规则在 service 层，可单测、可复用（HTTP 入口、定时任务、后台 job 都能调）。
- Agent 节点里的"轻规则"（阈值、关键词）进一步抽到 `agents/*/policy.py`，节点变薄。

## 7. 与外部系统的对接

- **一期广告审批系统**：通过审批闸门对接，骨架阶段只在 `suggestion["involves_money"]=True` 标记，二期补审批单创建 + 回调执行。
- **LLM Provider**：`infras/llm.py` 抽象，OpenAI 兼容协议；business_chat 子图在 build 时注入。
- **MySQL / Redis**：`infras/database.py`、`infras/cache.py`，启动时初始化。
