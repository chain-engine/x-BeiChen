# 北辰 x-BeiChen（Agent 编排平台）

面向「广告联盟商务自动化 SaaS + 出海营销智能平台」的多 Agent 编排平台：用 LangGraph 编排 Agent 协作、LangChain 组装模型能力、映射表路由任务派发，资金类操作统一过审批闸门。

[English](README.en.md) | 中文

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-1C3C3C)
![LangChain](https://img.shields.io/badge/LangChain-0.3%2B-1C3C3C?logo=langchain&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-D71F00?logo=sqlalchemy&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-5.0%2B-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-24.0%2B-2496ED?logo=docker&logoColor=white)
![uv](https://img.shields.io/badge/uv-0.5%2B-6E40C9)

![Stars](https://img.shields.io/github/stars/yeyushilai/x-BeiChen?label=Stars)
![Forks](https://img.shields.io/github/forks/yeyushilai/x-BeiChen?label=Forks)
![License](https://img.shields.io/github/license/yeyushilai/x-BeiChen?label=License)
![月提交数](https://img.shields.io/github/commit-activity/m/yeyushilai/x-BeiChen?label=Commits)

## 💡 项目介绍

北辰是基于 **LangGraph + LangChain** 的 Agent 编排平台，承载两大业务方向：

- **广告联盟商务自动化 SaaS**：商务对话 Agent 自动接待客户咨询（RAG 政策问答）、数据监控 Agent 自动巡检投放数据并告警建议、客户管理与任务调度自动出报表；
- **出海营销智能平台**：内容创作 Agent 生成多语言素材、客服转化 Agent 引导成交、投放洞察 Agent 总结素材表现与竞品动态。

平台坚持三条工程铁律：**资金操作必过审批闸门**（审批写工具 + 审批单留痕）、**事件全链路可审计**（事件总线 + 落库）、**Agent 回答有依据**（RAG 检索带来源溯源）。一期广告审批系统为独立项目，北辰通过审批闸门与其对接。

## 🚀 快速开始

### 1. 环境要求

| 系统 | 要求 |
| --- | --- |
| **Windows** | Windows 10+ / PowerShell 5.1+；安装 [Python 3.11+](https://www.python.org/downloads/) 与 [uv](https://docs.astral.sh/uv/) |
| **Linux** | Ubuntu 22.04+ / CentOS 8+；`apt install python3.11 python3.11-venv` 或使用 pyenv |
| **macOS** | macOS 13+；`brew install python@3.11 uv` |

> 数据库（MySQL）与缓存（Redis）非强制：骨架阶段 `DATABASE_ENABLED=false`、`REDIS_ENABLED=false` 即可本地运行，业务接口会返回 503 提示开启方式。

### 2. 项目代码克隆

```bash
git clone https://github.com/yeyushilai/x-BeiChen.git
cd x-BeiChen/server
```

### 3. 依赖同步安装

```bash
uv sync          # 标准安装并锁定依赖（生成 uv.lock）
# 或使用已预置的虚拟环境：python -m venv .venv && .venv/Scripts/pip install -r <由 uv lock 导出>
```

### 4. 环境配置

创建 `.env`（复制自 `.env.example`）：

```bash
cp .env.example .env
```

核心参数说明：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `APP_ENV` | `development` | 运行环境：development / testing / production |
| `SERVER_PORT` | `6666` | 服务监听端口 |
| `DATABASE_ENABLED` | `false` | 是否启用 MySQL（启用后自动建表） |
| `DATABASE_HOST` | `localhost` | MySQL 地址 |
| `REDIS_ENABLED` | `false` | 是否启用 Redis（缓存 / 事件总线 / 检查点） |
| `AI_LLM_API_KEY` | 空 | 配置后自动从 Mock 切换到真实模型（OpenAI 兼容协议） |
| `AI_LLM_BASE_URL` | 方舟 v3 | LLM 服务地址，可对接豆包方舟 / DeepSeek / 本地 vLLM |
| `AGENT_CHECKPOINT` | `memory` | Agent 检查点：memory（开发）/ redis（生产） |
| `BEICHEN_SCHEDULER_ENABLED` | `false` | 定时任务开关（监控巡检 15 分钟/轮） |

### 5. 服务启动

**方式一：本地开发热重载**

```bash
uv run uvicorn src.main:app --reload --port 6666
```

**方式二：Docker 容器部署**

```bash
docker build -t x-beichen-server .
docker run -p 6666:6666 --env-file .env x-beichen-server
```

启动后访问接口文档：<http://127.0.0.1:6666/docs>

### 6. 常用工程命令

```bash
# 单元测试
uv run pytest

# 代码格式化
uv run ruff format src

# 静态代码检查
uv run ruff check src
uv run mypy src

# 依赖漏洞扫描
uv run pip-audit

# 编排层端到端自检（无需数据库，验证 3 条核心链路）
uv run python scripts/verify_agent_flow.py
```

### 7. 使用方法示例

提交一个数据监控任务（自动巡检并触发告警建议）：

```bash
curl -X POST http://127.0.0.1:6666/api/admin/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_type": "monitor", "payload": {"account_id": "acc_001", "campaign_id": "camp_001"}}'
```

响应中的 `events` 会包含 `suggestion_created` 建议事件；若建议涉及资金操作，`approval_no` 保持为空——由审批闸门（二期对接广告审批系统）接管，资金操作不直接执行。

### 8. 常见问题排查

| 现象 | 原因与解决 |
| --- | --- |
| 端口被占用 `address already in use` | 换端口：`--port 8001`，或 `lsof -i:6666`（macOS/Linux）/ `netstat -ano \| findstr 6666`（Windows）定位占用进程 |
| `uv` 命令不存在 | 安装 uv：`pip install uv` 或 `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| 业务接口返回 503 | 数据库未启用：设置 `DATABASE_ENABLED=true` 并配置 `DATABASE_HOST/PORT/USER/PASSWORD/DATABASE` |
| 数据库连接失败 `Can't connect to MySQL server` | 确认 MySQL 已启动、账号有权限；本机首次建议先 `init_database()` 建表 |
| 配置未生效 | 配置优先级：环境变量 > `config.{env}.yaml` > `config.yaml` > 代码默认值；检查 `.env` 是否复制且键名正确 |
| LLM 回复为 mock 内容 | 未配置 `AI_LLM_API_KEY`，配置后自动切换真实模型 |

## 📁 项目结构

```
server/
├── src/
│   ├── main.py              # 应用入口：create_app / lifespan / 中间件与路由装配
│   ├── api/                 # API 接口层：HTTP 接入、参数解析、依赖装配
│   │   ├── dependencies.py  # 公共依赖注入（DB 会话、服务装配）
│   │   ├── response.py      # 统一响应（ApiResponse 包装：code/message/data/timestamp）
│   │   ├── router.py        # 中央路由（/api/admin/...）
│   │   └── admin/v1/        # 路由组：health / auth(预留) / agents / monitoring
│   ├── services/            # 业务逻辑层：规则与事务编排（禁读 Request）
│   │   ├── agent_orchestrator_service.py  # 任务提交/查询/人工接管/事件落库
│   │   └── monitoring_service.py         # 巡检触发 / 告警查询
│   ├── repositories/        # 数据访问层：纯 CRUD，无业务判断
│   │   ├── base_repository.py            # 通用 CRUD 基类
│   │   ├── agent_task_repository.py      # Agent 任务表访问
│   │   └── agent_event_repository.py     # 协作事件表访问
│   ├── models/entities/     # SQLAlchemy ORM 实体
│   │   ├── agent_task.py    # agent_tasks 任务表（状态机/重试/审批单号）
│   │   └── agent_event.py   # agent_events 事件表（审计留痕）
│   ├── agents/              # Agent 编排层（LangGraph + LangChain 标准实现）
│   │   ├── orchestrator.py  # 顶层调度中枢：route → 子图节点 → aggregate
│   │   ├── registry.py      # Agent 注册表（映射表路由：派给谁）
│   │   ├── runtime.py       # 运行时：checkpointer / invoke / resume（断点续跑）
│   │   ├── state.py         # 状态 TypedDict（顶层与子图合并契约）
│   │   ├── base.py          # BaseAgent 抽象基类（子图构建契约）
│   │   ├── tools/           # 工具注册中心（只读/审批写/执行写 三级权限）
│   │   ├── monitor/         # 数据监控 Agent 子图
│   │   └── business_chat/   # 商务对话 Agent 子图
│   ├── infras/              # 基础设施层：database / http / cache / event_bus / llm
│   ├── schemas/             # Pydantic 模型：统一响应 / Agent 任务入出参
│   ├── constants/           # 常量与枚举（含 Agent 编排域枚举）
│   ├── core/                # 全局支撑：config / logger / exceptions / middleware
│   ├── scheduling/          # 定时任务（APScheduler 监控巡检）
│   ├── templates/prompts/   # 提示词模板（与节点代码分离，便于运营迭代）
│   └── utils/               # 无状态工具：helpers（脱敏/路径）/ convert（类型转换）
├── scripts/
│   └── verify_agent_flow.py # 编排层端到端自检脚本
├── pyproject.toml           # 项目元数据与依赖声明（uv）
├── .env.example             # 环境变量示例
├── config.yaml.example      # YAML 配置示例（复制为 config.yaml）
└── Dockerfile               # 容器镜像定义
```

## 🏗️ 系统架构

### 系统分层架构

```mermaid
flowchart TB
    subgraph Web["接入层（web/ 独立仓库）"]
        W1["管理后台前端"]
        W2["客户触点（IM / Web）"]
    end

    subgraph API["API 接口层（api/）"]
        A1["/api/admin/v1：health / agents / tasks / monitoring"]
        A2["统一响应 + 全局异常"]
    end

    subgraph ORCH["Agent 编排层（agents/）"]
        C1["顶层编排图：route → 子图节点 → aggregate"]
        C2["业务子图：数据监控 / 商务对话"]
        C3["Agent 注册表（映射表路由）"]
        C4["工具注册中心（三级权限）"]
    end

    subgraph BIZ["业务逻辑层（services/）"]
        D1["AgentOrchestratorService"]
        D2["MonitoringService"]
    end

    subgraph DATA["数据访问层（repositories/ + models/）"]
        E1["agent_tasks / agent_events"]
    end

    subgraph INFRA["基础设施层（infras/ + core/）"]
        F1["MySQL 连接池"]
        F2["Redis（缓存 / 事件总线 / 检查点）"]
        F3["LLM Provider（LangChain）"]
        F4["日志 / 配置 / 异常 / 中间件"]
    end

    Web --> API --> BIZ --> DATA
    BIZ --> ORCH
    ORCH --> INFRA
    DATA --> INFRA
```

### 核心业务流程：Agent 任务编排

```mermaid
flowchart LR
    Start([提交任务]) --> Route["route 节点<br>映射表路由（task_type → Agent）"]
    Route -->|monitor| Sub1["数据监控子图"]
    Route -->|business_chat| Sub2["商务对话子图"]
    Sub1 --> Agg["aggregate 聚合<br>（状态 / 结果 / 事件归一化）"]
    Sub2 --> Agg
    Agg --> DB[("任务 / 事件落库<br>审计留痕")]
    Sub2 -->|投诉 / 需人工| Int["interrupt 人工接管<br>（LangGraph 断点暂停）"]
    Int -->|resume 人工决策| Sub2
```

### 核心业务流程：数据监控巡检

```mermaid
flowchart TD
    Pull["拉取投放数据（只读工具）"] --> Calc["计算指标（消耗 / CPC / 预算占用率）"]
    Calc --> Judge{"judge 条件边<br>是否异常？"}
    Judge -->|"正常（normal）"| Normal["结束，进入下一轮巡检"]
    Judge -->|"异常（alert）"| Alert["告警 + 发布建议事件"]
    Alert --> Money{"建议涉及资金写？"}
    Money -->|"是"| Approval["审批闸门（广告审批系统对接，二期）<br>Agent 不直接执行"]
    Money -->|"否"| Done["结束"]
```

### 关键技术组件说明

| 组件 | 职责 | 实现要点 |
| --- | --- | --- |
| 顶层编排图 | 派活链路、子图生命周期、结果聚合 | LangGraph `StateGraph`；编译子图直接注册为节点；条件边动态路由 |
| Agent 注册表 | 「派给谁」的静态映射 | `task_type → AgentSpec` 映射表；子图惰性编译 + 缓存 |
| Agent 运行时 | 执行与恢复 | `checkpointer`（memory/redis）；`Command(resume=...)` 断点续跑 |
| 工具注册中心 | Agent 外部能力 + 权限 | 三级权限：只读 / 审批写 / 执行写；权限不足抛授权异常 |
| 事件总线 | Agent 间协作消息通道 | `InMemoryEventBus`（骨架）/ `RedisStreamEventBus`（生产预留） |
| RAG 检索 | 政策 / FAQ 知识底座 | 骨架为 mock 命中；二期接向量库，回复带来源溯源 |

## 🛠️ 技术栈

| 分类 | 选型 |
| --- | --- |
| 开发语言 | Python 3.11+ |
| Web 框架 | FastAPI 0.115+ / Uvicorn |
| Agent 编排 | LangGraph 0.2+（顶层编排图 + 业务子图嵌套） |
| LLM 接入 | LangChain（langchain-core / langchain-openai，OpenAI 兼容协议） |
| 数据存储 | MySQL 8.0（SQLAlchemy 2 + PyMySQL，Alembic 迁移） |
| 缓存 | Redis 5.0+（可选；骨架默认内存实现） |
| 消息/事件 | 内存事件总线（骨架）/ Redis Stream（生产预留） |
| 配置 | dataclass + PyYAML + python-dotenv |
| 日志 | loguru（文件恒 JSON，request_id 注入） |
| 定时任务 | APScheduler（AsyncIOScheduler） |
| 包管理 | uv（pyproject.toml + uv.lock） |
| 部署运维 | Docker / docker-compose |

## 📖 API 文档说明

启动服务后访问：

| 文档 | 地址 |
| --- | --- |
| Swagger 交互式文档 | <http://127.0.0.1:6666/docs> |
| ReDoc 只读文档 | <http://127.0.0.1:6666/redoc> |
| OpenAPI JSON 规范 | <http://127.0.0.1:6666/openapi.json> |

核心接口清单（管理后台，前缀 `/api/admin/v1`）：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/health` | 健康探针（含 db / redis / agent_runtime 依赖状态） |
| GET | `/version` | 应用版本信息 |
| POST | `/auth/login` | 登录（预留：二期 JWT + RBAC） |
| GET | `/agents` | Agent 注册表列表 |
| POST | `/tasks` | 提交 Agent 任务（task_type + payload） |
| GET | `/tasks` | 任务列表（status / task_type 过滤，分页） |
| GET | `/tasks/{task_id}` | 任务详情 |
| POST | `/tasks/{task_id}/resume` | 人工接管恢复（interrupt/resume） |
| GET | `/events` | 协作事件列表（审计） |
| POST | `/monitoring/scan` | 手动触发数据监控巡检 |
| GET | `/monitoring/alerts` | 告警事件列表 |

**权限控制**：当前为骨架阶段，鉴权 / 限流 / 熔断 / 请求 ID 均已预留实现（`src/core/middleware.py`）但默认未启用；二期接入 JWT + RBAC 后，管理后台接口需携带 `Authorization` 头访问。

## 💾 存储配置说明

### 数据库存储（MySQL，`DATABASE_ENABLED=true` 时启用）

| 表 | 说明 | 关键字段 |
| --- | --- | --- |
| `agent_tasks` | Agent 任务表（状态机 / 重试 / 线程 ID） | `task_type`、`status`、`thread_id`、`retry_count`、`approval_no`、`result(JSON)` |
| `agent_events` | 协作事件表（审计留痕） | `event_type`、`source_agent`、`payload(JSON)` |

配置：`DATABASE_HOST / PORT / USER / PASSWORD / DATABASE`；启用后调用 `init_database()` 自动建表。

### 缓存存储（Redis，可选）

`REDIS_ENABLED=true` 时启用，用途：Agent 检查点（`AGENT_CHECKPOINT=redis`）、事件总线（Redis Stream）、任务幂等去重。骨架阶段默认使用进程内内存实现。

### 本地文件存储

- 日志文件：`server/logs/x-BeiChen-{time}.log`（loguru 写入，恒为 JSON 格式，自动轮转/压缩）；
- 配置读取：`server/config.yaml`（或 `config.{env}.yaml`，如 `config.production.yaml`）。

## 📜 许可证

本项目基于 [MIT License](../LICENSE) 开源协议发布（Copyright © 2026 John Young）。

## 🔗 参考资料

| 依赖 | 官方文档 |
| --- | --- |
| Python | <https://docs.python.org/3/> |
| uv | <https://docs.astral.sh/uv/> |
| FastAPI | <https://fastapi.tiangolo.com/> |
| LangGraph | <https://langchain-ai.github.io/langgraph/> |
| LangChain | <https://python.langchain.com/docs/> |
| SQLAlchemy | <https://docs.sqlalchemy.org/en/20/> |
| Redis | <https://redis.io/docs/> |
| loguru | <https://loguru.readthedocs.io/> |
| Docker | <https://docs.docker.com/> |

## 📧 联系方式

- 作者：John Young（夜雨诗来）
- 邮箱：john.young@foxmail.com
- Gitee：<https://gitee.com/yeyushilai>
- GitHub：<https://github.com/yeyushilai>
- 项目地址：待补充
