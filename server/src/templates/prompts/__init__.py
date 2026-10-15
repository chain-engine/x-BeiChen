"""提示词模板包（北辰 x-BeiChen）。"""

from src.templates.prompts.business_chat_prompts import (
    CHAT_REPLY_PROMPT,
    INTENT_CLASSIFY_PROMPT,
)
from src.templates.prompts.monitor_prompts import ANOMALY_JUDGE_PROMPT, MONITOR_SYSTEM_PROMPT

__all__ = [
    "MONITOR_SYSTEM_PROMPT",
    "ANOMALY_JUDGE_PROMPT",
    "INTENT_CLASSIFY_PROMPT",
    "CHAT_REPLY_PROMPT",
]
