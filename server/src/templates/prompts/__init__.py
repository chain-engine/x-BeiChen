#!/usr/bin/env python3
"""提示词模板加载器（北辰 x-BeiChen）。

提示词以 YAML 文件存放在本目录，业务代码通过 get_messages / render_messages 取用，
调整文案不改代码。YAML 结构：

    <prompt_key>:
      description: 用途说明
      messages:
        - role: system | human
          content: 文本，{var} 为运行时占位
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_PROMPTS_DIR = Path(__file__).parent


@lru_cache(maxsize=1)
def _load_all() -> dict[str, Any]:
    """扫描目录下所有 *.yaml 合并加载（进程级缓存，改文件需重启）。"""
    data: dict[str, Any] = {}
    for yml in sorted(_PROMPTS_DIR.glob("*.yaml")):
        with yml.open("r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
        if not isinstance(loaded, dict):
            continue
        data.update(loaded)
    return data


def get_prompt(key: str) -> dict[str, Any]:
    """取整条 prompt 配置（含 description / messages）。"""
    data = _load_all()
    if key not in data:
        raise KeyError(f"prompt '{key}' not found under {_PROMPTS_DIR}")
    return data[key]


def get_messages(key: str) -> list[dict[str, str]]:
    """取原始 messages（未渲染变量）。"""
    return get_prompt(key).get("messages", [])


def render_messages(key: str, **vars: Any) -> list[dict[str, str]]:
    """渲染 messages 中的 {var} 占位符，返回 [{role, content}, ...]，可直接喂给 ChatPromptTemplate.from_messages。"""
    out: list[dict[str, str]] = []
    for m in get_messages(key):
        content = m["content"]
        if vars:
            content = content.format_map(_SafeDict(vars))
        out.append({"role": m["role"], "content": content})
    return out


class _SafeDict(dict):
    """format_map 兜底：未提供的变量原样保留 {var}，不抛 KeyError。"""

    def __missing__(self, key: str) -> str:  # noqa: D401
        return "{" + key + "}"


__all__ = ["get_prompt", "get_messages", "render_messages"]
