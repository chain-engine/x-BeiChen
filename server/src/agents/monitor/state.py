#!/usr/bin/env python3
"""数据监控 Agent 子图状态（北辰 x-BeiChen）。

继承顶层共享字段（status/result/error/events/approval_no 用于回传合并），
扩展监控域私有字段（raw/metric/anomaly），仅存在于子图内部。
"""

from __future__ import annotations

from typing import Any, TypedDict


class MonitorState(TypedDict, total=False):
    """数据监控子图状态。"""

    # ── 顶层共享字段（回传合并契约）──
    task_id: int
    task_type: str
    payload: dict[str, Any]
    status: str
    result: dict[str, Any] | None
    error: str | None
    events: list[dict[str, Any]]
    approval_no: str | None

    # ── 监控域私有字段 ──
    raw: dict[str, Any] | None      # 拉取到的原始投放数据
    metric: dict[str, Any] | None   # 计算后的指标（CPC / ROAS / 环比）
    anomaly: bool                   # 是否判定为异常
    suggestion: dict[str, Any] | None  # 异常时生成的处置建议（含是否涉及资金写）
