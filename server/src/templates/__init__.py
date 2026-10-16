"""提示词模板包（北辰 x-BeiChen）。

提示词以 YAML 文件存放在 prompts/ 目录，通过本包暴露的 loader 取用：
    from src.templates import render_messages, get_messages

    messages = render_messages("chat_reply", question=..., knowledge=...)
"""

from src.templates.prompts import get_messages, get_prompt, render_messages

__all__ = ["get_prompt", "get_messages", "render_messages"]
