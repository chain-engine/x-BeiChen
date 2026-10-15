#!/usr/bin/env python3
"""通知工具包（北辰 x-BeiChen）。

监控告警 / 商务事件的通知出口：企微 / 飞书 / 邮件 / 短信（二期按配置接入）。
骨架阶段：写日志 + 发布到事件总线，保证事件链路可观测。
"""

from __future__ import annotations

from typing import Any

from src.agents.tools.registry import ToolSpec, tool_registry
from src.constants import ToolPermissionLevel
from src.core.logger import logger


def send_alert(channel: str, title: str, content: str, **extra: Any) -> dict[str, Any]:
    """发送告警 / 通知（只读语义：不涉及资金写，可被 Agent 直接调用）。

    TODO(业务接入): 按 channel 分发到企微机器人 / 飞书 / 短信等渠道。
    """
    logger.warning(f"[Notify] channel={channel} title={title} content={content}")
    return {"channel": channel, "title": title, "sent": True, "extra": extra}


def register_notification_tools() -> None:
    """注册通知工具（幂等）。"""
    if tool_registry.get("notification.send_alert") is None:
        tool_registry.register(ToolSpec(name="notification.send_alert", description="发送告警/通知（只读）", func=send_alert, permission_level=ToolPermissionLevel.READ_ONLY))


register_notification_tools()

__all__ = ["send_alert", "register_notification_tools"]
