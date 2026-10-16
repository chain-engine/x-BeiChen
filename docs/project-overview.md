# 北辰 x-BeiChen 项目说明

## 1. 项目定位

面向「广告联盟商务自动化 SaaS + 出海营销智能平台」的多 Agent 编排平台 monorepo：

- `server/`：后端，FastAPI + LangGraph + LangChain，已交付首个可运行骨架。
- `web/`：前端，规划中（客户触点 + 管理后台两套应用）。

## 2. 业务方向

### 2.1 广告联盟商务自动化 SaaS

- **商务对话 Agent**：自动接待客户咨询，RAG 政策问答，命中投诉/退款/转人工关键词时进入 interrupt 人工接管。
- **数据监控 Agent**：定时巡检投放数据（消耗 / CPC / 转化率 / 预算消耗率），超阈值告警并生成处置建议。
- **任务调度**：APScheduler 定时拉数、出报表。

### 2.2 出海营销智能平台（二期规划）

- 内容创作 Agent（多语言素材生成）。
- 客服转化 Agent（引导成交）。
- 投放洞察 Agent（素材表现、竞品动态总结）。

## 3. 工程铁律

1. **资金操作必过审批闸门**：Agent 不直接执行 `adjust_budget / pause_campaign` 等写操作，只生成 `suggestion`，审批通过后由执行器落地。
2. **事件全链路可审计**：每次任务产生结构化事件，落库（`agent_events`）+ 事件总线 publish 双写。
3. **Agent 回答有依据**：RAG 检索带来源编号（`P001 / P002 ...`），不编造知识。

## 4. 技术栈

| 分类 | 选型 |
| --- | --- |
| 语言 | Python 3.11+（实际 venv 3.13） |
| Web | FastAPI 0.115+ / Uvicorn |
| Agent 编排 | LangGraph 1.2+（顶层图 + 业务子图嵌套，interrupt/resume） |
| LLM | LangChain（OpenAI 兼容协议，默认小米 MiMo） |
| 存储 | MySQL 8.0（SQLAlchemy 2 + PyMySQL，启动自动建表） |
| 缓存 | Redis 5.0+（可选，骨架用内存实现） |
| 定时任务 | APScheduler（AsyncIOScheduler） |
| 包管理 | uv（pyproject.toml + uv.lock） |

## 5. 快速开始

```bash
git clone https://github.com/chain-engine/x-BeiChen.git
cd x-BeiChen/server
uv sync
uv run x-BeiChen     # 监听 6666，开发模式热重载
```

环境变量见 `server/.env.example`，至少需要配置 MySQL DSN。

## 6. 自检

后端根目录跑：

```bash
.\.venv\Scripts\python.exe scripts\verify_agent_flow.py
```

覆盖三条链路：
1. monitor 告警分支（pull → calc → judge → alert）。
2. business_chat 正常咨询（intent → retrieve → generate）。
3. interrupt + resume 人工接管（投诉关键词 → 暂停 → resume 恢复）。

三条全绿表示编排层无回归。

## 7. 当前状态

- ✅ 后端骨架：API 骨架、Agent 编排层、子图、工具注册、事件双写、checkpointer。
- ✅ 提示词外置：`server/src/templates/prompts/*.yaml`，运营可调文案不改代码。
- ✅ 策略外置：`agents/*/policy.py`（阈值、关键词）、`agents/approval.py`（资金铁律）。
- ⏳ 管理后台前端：规划中，见 `web/README.md`。
- ⏳ 审批闸门对接：一期广告审批系统独立项目，二期补审批单落地。
- ⏳ RAG 知识库：当前为 mock 数据，二期接 Milvus + embedding。

## 8. 目录速览

```
x-BeiChen/
├── server/         # 后端
│   ├── src/
│   │   ├── api/         # HTTP 入口
│   │   ├── services/    # 业务编排
│   │   ├── repositories/# 数据访问
│   │   ├── agents/      # Agent 编排层（核心）
│   │   ├── models/      # ORM
│   │   ├── infras/      # DB / 缓存 / LLM / 事件总线
│   │   ├── templates/   # 提示词（yaml）
│   │   └── constants/  # 枚举
│   ├── scripts/         # 自检脚本
│   └── tests/
├── web/            # 前端（规划）
├── docs/           # 项目文档（架构 / 教程）
└── README.md
```
