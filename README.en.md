# BeiChen x-BeiChen (Multi-Agent Orchestration Platform)

A multi-agent orchestration platform monorepo for **government & enterprise customers**: `server/` (backend, LangGraph + LangChain orchestration core delivered) and `web/` (frontend: customer touchpoint + admin console, planned).

[中文](README.md) | English

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-1.2%2B-1C3C3C)
![LangChain](https://img.shields.io/badge/LangChain-0.3%2B-1C3C3C?logo=langchain&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-D71F00?logo=sqlalchemy&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-5.0%2B-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-24.0%2B-2496ED?logo=docker&logoColor=white)
![uv](https://img.shields.io/badge/uv-0.5%2B-6E40C9)

![Stars](https://img.shields.io/github/stars/chain-engine/x-BeiChen?label=Stars)
![Forks](https://img.shields.io/github/forks/chain-engine/x-BeiChen?label=Forks)
![License](https://img.shields.io/github/license/chain-engine/x-BeiChen?label=License)
![Monthly Commits](https://img.shields.io/github/commit-activity/m/chain-engine/x-BeiChen?label=Commits)

## 💡 Introduction

BeiChen is a multi-agent orchestration platform for government & enterprise customers (e.g., public services, HR & social security, enterprise services), built on **LangGraph + LangChain**:

- **Orchestration core**: top-level hub graph (route → subgraph node → aggregate) + Agent registry (explicit / LLM dynamic / hybrid routing) + runtime (checkpointer / invoke / resume with checkpoint-based human takeover);
- **Plug-in business agents**: every business agent implements `BaseAgent` and registers into the registry — it is then automatically covered by top-level routing, task dispatch, human takeover and event audit, with no changes to the orchestration layer;
- **Engineering rules**: money-related writes always pass the approval gate, full event traceability (dual-write: persist + publish), and evidence-grounded answers (RAG knowledge base reserved; vector store + source citations in phase 2).

**Current status**: the `server/` orchestration skeleton is delivered and runs standalone; the previous fixed-workflow agents (data monitoring / business chat / customer management) have been removed along with the repositioning — the registry is empty, and new business agents register to extend; the `web/` frontend is planned.

## 🚀 Quick Start

```bash
git clone https://github.com/chain-engine/x-BeiChen.git
cd x-BeiChen/server
uv sync
uv run x-BeiChen     # one-shot start: dev hot-reload on, listens on 8866
```

Detailed requirements, configuration (`.env`), startup options, API and extension guide: **[server/README.md](server/README.md)**.

## 🧭 Frontend Plan (web/)

BeiChen plans two frontend applications, neither started yet (see `web/README.md`):

| App | Users | Responsibility |
| --- | --- | --- |
| Admin console | Operations / management | Task panel, agent registry, event audit, health monitoring |
| Gov & enterprise touchpoint | Customers / end users | IM / Web / App: business consultation, service interaction |

## 📁 Project Structure

```text
x-BeiChen/
├── server/                  # Backend (FastAPI + LangGraph + LangChain, orchestration skeleton delivered)
│   ├── src/                 # Source (strict api → services → repositories flow)
│   │   ├── api/             # API layer: routers / dependency injection / response wrapper
│   │   ├── services/        # Business logic: Agent task facade
│   │   ├── repositories/    # Data access: task / event repositories
│   │   ├── agents/          # Agent orchestration: graph / registry / runtime / routing / tools
│   │   ├── models/          # ORM entities (agent_tasks / agent_events)
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── core/            # Config / logging / exceptions / middleware
│   │   ├── infras/          # Database / cache / event bus / LLM provider
│   │   ├── scheduling/      # APScheduler generic scheduler (business jobs TBD)
│   │   ├── constants/       # Enums & constants (agent orchestration domain)
│   │   └── templates/       # Prompt templates (routing prompts)
│   ├── tests/               # Test directory (to be filled with business access)
│   └── README.md            # Backend detailed docs (quick start / architecture / API / extension)
├── web/                     # Frontend (planned, see web/README.md)
├── docker-compose.yml       # Container orchestration (placeholder)
└── LICENSE                  # MIT License
```

## 🏗️ System Architecture

Whole-product view: two frontends + one backend; the approval service is a phase-2 separate system connected via the approval gate.

```mermaid
flowchart TB
    subgraph FE["Frontend (web/, planned)"]
        A1["Gov & enterprise touchpoint (IM / Web / App)"]
        A2["Admin console"]
    end

    subgraph BE["BeiChen backend (server/, orchestration skeleton delivered)"]
        B1["API layer (api/admin/v1)"]
        B2["Service layer (services/)"]
        B3["Agent orchestration (agents/)"]
        B4["Repository layer (repositories/)"]
    end

    subgraph INFRA["Infrastructure"]
        C1[("MySQL")]
        C2[("Redis (optional)")]
        C3["LLM Provider (LangChain)"]
        C4["Event bus (dual-write)"]
    end

    subgraph EXT["External systems"]
        D1["Approval service (phase-2, separate project)"]
    end

    A1 --> B1
    A2 --> B1
    B1 --> B2
    B2 --> B3
    B3 --> B4
    B4 --> C1
    B3 --> C2
    B3 --> C3
    B3 -.-> C4
    B2 -. Approval gate .-> D1
```

Agent orchestration core (LangGraph top-level graph with nested business subgraphs, dynamically mounted from the registry):

```mermaid
flowchart LR
    START --> ROUTE["route (registry routing)<br/>explicit / llm / hybrid"]
    ROUTE -->|"registered business agent"| SUB["business subgraph node<br/>(nodes + conditional edges + state machine)"]
    SUB --> AGG["aggregate"]
    AGG --> END
    ROUTE -->|"unregistered / routing failed"| FAIL["task failed (error written back)"]
    FAIL --> END
```

## 🛠️ Tech Stack

| Category | Choice |
| --- | --- |
| Backend language | Python 3.11+ |
| Web framework | FastAPI 0.115+ / Uvicorn |
| Agent orchestration | LangGraph 1.2+ (top-level graph + nested subgraphs, interrupt/resume) |
| LLM integration | LangChain (langchain-core / langchain-openai, OpenAI-compatible; defaults to Xiaomi MiMo) |
| Data storage | MySQL 8.0 (SQLAlchemy 2 + PyMySQL, auto table creation on startup) |
| Cache | Redis 5.0+ (optional; in-memory by default in skeleton) |
| Messaging/Events | In-memory event bus (skeleton, dual-write: persist + publish) / Redis Stream (prod reserved) |
| Scheduling | APScheduler (AsyncIOScheduler, generic scheduler) |
| Package management | uv (pyproject.toml + uv.lock) |
| Frontend (planned) | TBD (candidates: Vue 3 / React + Vite, see web/README.md) |

## 📄 License

[MIT License](LICENSE) © 2026 John Young

## 📮 Contact

- **Author**: John Young (夜雨诗来)
- **Email**: john.young@foxmail.com
- **Gitee**: https://gitee.com/yeyushilai
- **GitHub**: https://github.com/yeyushilai
- **Repository URL**: [https://github.com/chain-engine/x-BeiChen](https://github.com/chain-engine/x-BeiChen)
