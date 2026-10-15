#!/usr/bin/env python3
"""北辰 x-BeiChen 编排层端到端自检脚本（无数据库依赖）。

验证三条核心链路：
    1. 数据监控 Agent：pull → calc → judge（条件边：正常/告警）→ 告警+事件发布
    2. 商务对话 Agent：intent → RAG retrieve → generate（mock 回复 + 来源溯源）
    3. 人工接管链路：interrupt 暂停 → resume 恢复（LangGraph 断点续跑）

运行：python scripts/verify_agent_flow.py
"""

from __future__ import annotations

import sys
import traceback
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> int:
    from src.agents.runtime import get_agent_runtime

    runtime = get_agent_runtime()
    orchestrator = runtime.build_orchestrator()

    # ── 链路 1：数据监控（mock 消耗 65% 预算 → 触发告警分支）──
    print("=" * 56)
    print("[1] 数据监控 Agent：judge 条件边 → 告警分支")
    state = runtime.invoke_task(
        "monitor",
        {"account_id": "acc_test", "campaign_id": "camp_001"},
    )
    assert state["status"] == "success", f"monitor 应成功，实际 {state['status']}"
    events = [e.get("type") for e in state.get("events", [])]
    assert "suggestion_created" in events, f"应产生建议事件，实际 {events}"
    print(f"    status  : {state['status']}")
    print(f"    metric  : {state['result']['metric']}")
    print(f"    suggestion: {state['result']['suggestion']}")
    print(f"    events  : {events}")
    print(f"    approval_no: {state.get('approval_no')}（资金写未直接执行 → None，走审批）")

    # ── 链路 2：商务对话（正常咨询 → RAG mock 检索 + 来源溯源）──
    print("=" * 56)
    print("[2] 商务对话 Agent：intent → RAG retrieve → generate")
    state2 = runtime.invoke_task(
        "business_chat",
        {"customer_id": "cust_001", "message": "请问结算周期多久？"},
    )
    assert state2["status"] == "success", f"business_chat 应成功，实际 {state2['status']}"
    print(f"    status : {state2['status']}")
    print(f"    reply  : {(state2['result'] or {}).get('reply')}")
    print(f"    sources: {(state2['result'] or {}).get('sources')}")

    # ── 链路 3：人工接管（投诉 → interrupt 暂停 → resume 恢复）──
    print("=" * 56)
    print("[3] 人工接管链路：interrupt 断点 → resume 续跑")
    thread = f"resume_demo:{uuid.uuid4().hex[:6]}"
    initial = {
        "task_id": 999,
        "task_type": "business_chat",
        "payload": {"customer_id": "cust_003", "message": "我要投诉，转人工！"},
        "target_agent": None,
        "status": "running",
        "result": None,
        "error": None,
        "events": [],
        "approval_no": None,
    }
    config = {"configurable": {"thread_id": thread}}
    paused = orchestrator.invoke(initial, config=config)
    print(f"    第一轮（interrupt 暂停）: status={paused.get('status')}")
    assert paused.get("status") == "running", "interrupt 后应处于暂停态（running）"
    resumed = runtime.resume_task(thread, {"decision": "approve", "remark": "人工已介入处理投诉"})
    print(f"    第二轮（resume 恢复）  : status={resumed.get('status')}")
    print(f"    reply: {resumed.get('result')}")
    assert resumed.get("status") == "success", "resume 后应完成执行（success）"

    print("=" * 56)
    print("✓ 三条链路全部验证通过")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
