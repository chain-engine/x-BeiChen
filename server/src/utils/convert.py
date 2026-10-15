#!/usr/bin/env python3
"""类型转换工具（环境变量字符串 → 原生类型）。

供 core/config.py 在加载环境变量时做类型转换使用，避免配置解析报错。
"""

from __future__ import annotations

from typing import Any

def to_bool(value: Any, default: bool = False) -> bool:
    """字符串/任意值 → bool。

    兼容 "true/false/1/0/yes/no/on/off"（大小写不敏感），
    无法识别时返回 default，绝不抛异常。

    Args:
        value: 待转换值
        default: 无法识别时的默认值

    Returns:
        bool: 转换结果
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "on"}:
        return True
    if text in {"false", "0", "no", "n", "off"}:
        return False
    return default

def to_int(value: Any, default: int = 0) -> int:
    """任意值 → int，失败回退 default。

    Args:
        value: 待转换值
        default: 转换失败时的默认值

    Returns:
        int: 转换结果
    """
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default

def to_float(value: Any, default: float = 0.0) -> float:
    """任意值 → float，失败回退 default。

    Args:
        value: 待转换值
        default: 转换失败时的默认值

    Returns:
        float: 转换结果
    """
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default
