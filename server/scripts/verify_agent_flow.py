#!/usr/bin/env python3
"""北辰 x-BeiChen 编排层端到端自检脚本（无数据库依赖）。

验证四条核心链路：
    1. 数据监控 Agent：pull → calc → judge（条件边：正常/告警）→ 告警+事件发布
    2. 商务对话 Agent：intent → RAG retrieve → generate（mock 回复 + 来源溯源）
    3. 人工接管链路：interrupt 暂停 → resume 恢复（LangGraph 断点续跑）
    4. 客户管理 Agent（演示）：fetch → evaluate → compose → dispatch
       （四步链路可跑通，产出演示数据、不发业务事件）

运行：python scripts/verify_agent_flow.py
"""

from __future__ import annotations

import os
import sys
import traceback
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 自检脚本声明"无数据库依赖"：强制离线模式，使 Agent 走 mock 快照（fetch 不读真实库）
os.environ["DATABASE_ENABLED"] = "false"
os.environ["REDIS_ENABLED"] = "false"


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
    assert "alert_raised" in events, f"应产生告警事件，实际 {events}"
    assert "suggestion_created" in events, f"应产生建议事件，实际 {events}"
    print(f"    status  : {state['status']}")
    print(f"    metric  : {state['result']['metric']}")
    print(f"    suggestion: {state['result']['suggestion']}")
    print(f"    events  : {events}")
    print(f"    target_agent: {state.get('target_agent')}（assignee_agent 回写依据）")
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
    paused = runtime.invoke_task(
        "business_chat",
        {"customer_id": "cust_003", "message": "我要投诉，转人工！"},
        thread_id=thread,
        task_id=999,
    )
    print(f"    第一轮（interrupt 暂停）: status={paused.get('status')}")
    assert paused.get("status") == "waiting_human", f"interrupt 后应处于等待人工，实际 {paused.get('status')}"
    assert "__interrupt__" not in paused, "返回状态不应残留不可序列化的 __interrupt__"
    interrupt_ctx = (paused.get("result") or {}).get("interrupt")
    assert interrupt_ctx is not None, "result 中应携带人工接管上下文"
    print(f"    interrupt 上下文: {interrupt_ctx}")
    resumed = runtime.resume_task(thread, {"decision": "approve", "remark": "人工已介入处理投诉"})
    print(f"    第二轮（resume 恢复）  : status={resumed.get('status')}")
    print(f"    reply: {resumed.get('result')}")
    assert resumed.get("status") == "success", "resume 后应完成执行（success）"

    # ── 链路 4：客户管理 Agent（演示）——四步链路可跑通、产出演示数据、不发业务事件 ──
    print("=" * 56)
    print("[4] 客户管理 Agent（演示）：fetch → evaluate → compose → dispatch")
    # 4a. 跟进巡检（scope=due_followup：演示客户 → 演示跟进任务）
    state4a = runtime.invoke_task(
        "customer",
        {"scope": "due_followup"},
    )
    assert state4a["status"] == "success", f"customer 应成功，实际 {state4a['status']}"
    assert state4a.get("target_agent") == "customer", f"assignee 应为 customer，实际 {state4a.get('target_agent')}"
    res4a = state4a.get("result") or {}
    followups = res4a.get("followups", [])
    assert followups and all(f.get("customer_id") for f in followups), f"演示链路应产出演示跟进任务，实际 {followups}"
    assert res4a.get("demo") is True, "演示模式 result 应带 demo=True 标记"
    ev4a = [e.get("type") for e in state4a.get("events", [])]
    assert ev4a == [], f"演示模式不应产生业务事件（避免污染审计），实际 {ev4a}"
    print(f"    status  : {state4a['status']}")
    print(f"    events  : {ev4a}（演示不发事件）")
    print(f"    followups（演示产出）: {followups}")

    # 4b. 报表（scope=report：演示任务清单含报表任务，result.demo 标记）
    state4b = runtime.invoke_task(
        "customer",
        {"scope": "report"},
    )
    assert state4b["status"] == "success", f"customer 报表应成功，实际 {state4b['status']}"
    res4b = state4b.get("result") or {}
    assert res4b.get("demo") is True, "报表任务同样为演示模式产出"
    ev4b = [e.get("type") for e in state4b.get("events", [])]
    assert ev4b == [], f"演示模式报表不应产生业务事件，实际 {ev4b}"
    print(f"    status  : {state4b['status']}")
    print(f"    events  : {ev4b}（演示不发事件）")
    print(f"    report  : {res4b.get('report')}（业务接入后由 ReportService 生成）")

    # 4c. 跟进判定规则校验（policy 确定性规则：跟进到期 → message 动作）
    from datetime import UTC, datetime, timedelta

    from src.agents.customer.policy import build_followup_actions
    from src.constants import CustomerStatus

    now = datetime.now(UTC)
    overdue_customer = {
        "customer_id": "rule_001",
        "status": CustomerStatus.LEAD.mark,
        "next_followup_at": now - timedelta(days=5),
    }
    ok_customer = {
        "customer_id": "rule_002",
        "status": CustomerStatus.LEAD.mark,
        "next_followup_at": now + timedelta(days=1),
    }
    acts_overdue = build_followup_actions(overdue_customer, now=now)
    acts_ok = build_followup_actions(ok_customer, now=now)
    assert any(a.get("action") == "message" for a in acts_overdue), f"跟进逾期应产出 message 动作，实际 {acts_overdue}"
    assert not any(a.get("involves_money") for a in acts_overdue), f"功能性 Agent 跟进动作不携带资金标记，实际 {acts_overdue}"
    assert acts_ok == [], f"未到期客户不应产出跟进动作，实际 {acts_ok}"
    print("    跟进判定规则: 逾期→message ✓ 未到期→无动作 ✓ 无资金标记 ✓")

    print("=" * 56)
    print("✓ 四条链路全部验证通过")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
