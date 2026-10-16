#!/usr/bin/env python3
"""北辰 x-BeiChen 命令行启动入口。

用法（项目根执行，等价于 uv run x-BeiChen）：
    uv run x-BeiChen                # 默认启动：开发环境自动开启热重载，读配置 host/port（8866）
    uv run x-BeiChen --reload       # 显式开启热重载（修改代码自动重启）
    uv run x-BeiChen --no-reload    # 显式关闭热重载（生产环境）
    uv run x-BeiChen --port 8866    # 覆盖监听端口
    uv run x-BeiChen --host 0.0.0.0 # 覆盖监听地址

热重载约定：
    - 默认行为跟随运行环境：development 且 debug=True → 自动开启热重载
    - 显式传 --reload / --no-reload 可覆盖默认行为
"""

from __future__ import annotations

import argparse
import sys
from typing import Any


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="x-BeiChen",
        description="北辰（BeiChen）Agent 编排平台后端启动器（FastAPI + Uvicorn）",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="监听地址（默认取配置 settings.server.host）",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="监听端口（默认取配置 settings.server.port，当前为 8866）",
    )
    parser.add_argument(
        "--reload",
        dest="reload",
        action="store_true",
        default=None,
        help="开启热重载（开发环境默认开启；显式指定以覆盖默认）",
    )
    parser.add_argument(
        "--no-reload",
        dest="reload",
        action="store_false",
        help="关闭热重载",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Worker 进程数（生产多进程部署；热重载模式强制为 1）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """启动北辰后端服务。"""
    args = _parse_args(argv)

    import uvicorn

    # 延迟加载配置：确保 .env / config.yaml 已加载后再启动
    from src.core.config import settings
    from src.core.logger import logger

    host = args.host or settings.server.host
    port = args.port or settings.server.port

    # 热重载：未显式指定时，开发环境 + debug=True 默认开启
    reload_enabled = args.reload if args.reload is not None else (settings.is_development and settings.server.debug)

    workers = args.workers or settings.server.workers
    if reload_enabled and workers != 1:
        logger.warning("热重载模式不支持多 Worker，已强制为 1")
        workers = 1

    if reload_enabled:
        logger.info(f"热重载已开启（APP_ENV={settings.app_env}）；修改代码后服务自动重启")
    logger.info(f"北辰后端启动：http://{host}:{port}  |  接口文档 http://{host}:{port}/docs")

    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=reload_enabled,
        workers=workers,
        log_level="info",
    )


if __name__ == "__main__":
    main(sys.argv[1:])
