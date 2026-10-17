#!/usr/bin/env python3
"""通用任务调度器（北辰 x-BeiChen）。

基于 APScheduler AsyncIOScheduler 的纯调度容器：只负责按 trigger 注册 / 启动 /
关闭可调用对象，**不 import、不认识任何具体业务 job**。业务 job 以函数引用在
装配层（scheduling/bootstrap.py）注入，新增/调整任务不改本类。

支持三类 trigger：
    - interval 周期（add_interval）：固定间隔重复跑
    - cron 定点（add_cron）：固定时刻跑
    - date 一次性（引擎已支持，本项目暂未使用）

与 FastAPI lifespan 联动：start() / shutdown()；默认不自动启动
（由 main.py 按 BEICHEN_SCHEDULER_ENABLED 开关注册），避免骨架阶段空转。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.core.logger import logger


class Scheduler:
    """通用任务调度器（单例容器）。

    只暴露注册原语与生命周期，不感知业务；start() 之后由 APScheduler
    按各 job 自己的 trigger 到点回调。
    """

    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

    # ----------------------------------------------------------
    # 注册原语（通用，业务 job 以函数引用传入）
    # ----------------------------------------------------------

    def add_interval(
        self,
        func: Callable,
        *,
        job_id: str,
        name: str,
        minutes: int = 0,
        hours: int = 0,
        kwargs: dict[str, Any] | None = None,
    ) -> None:
        """注册周期任务（interval）：幂等，已存在同 id 则跳过。

        Args:
            func: job 可调用对象（业务钩子，由装配层传入）
            job_id: 唯一任务标识（去重键）
            name: 任务显示名（日志/面板）
            minutes: 间隔分钟（与 hours 至少给一个）
            hours: 间隔小时
            kwargs: 透传给 job 的固定参数
        """
        if self._scheduler.get_job(job_id) is not None:
            return
        self._scheduler.add_job(
            func,
            trigger="interval",
            minutes=minutes,
            hours=hours,
            id=job_id,
            name=name,
            kwargs=kwargs or {},
            replace_existing=True,
        )
        logger.info(f"[Scheduler] 注册周期任务：{name}（{job_id}）间隔 {hours}h/{minutes}min")

    def add_cron(
        self,
        func: Callable,
        *,
        job_id: str,
        name: str,
        hour: int,
        minute: int = 0,
        kwargs: dict[str, Any] | None = None,
    ) -> None:
        """注册定点任务（cron）：每天固定时刻跑，幂等，已存在同 id 则跳过。

        Args:
            func: job 可调用对象（业务钩子，由装配层传入）
            job_id: 唯一任务标识（去重键）
            name: 任务显示名（日志/面板）
            hour: 定点小时（24h 制）
            minute: 定点分钟
            kwargs: 透传给 job 的固定参数
        """
        if self._scheduler.get_job(job_id) is not None:
            return
        self._scheduler.add_job(
            func,
            trigger="cron",
            hour=hour,
            minute=minute,
            id=job_id,
            name=name,
            kwargs=kwargs or {},
            replace_existing=True,
        )
        logger.info(f"[Scheduler] 注册定点任务：{name}（{job_id}）每天 {hour:02d}:{minute:02d}")

    # ----------------------------------------------------------
    # 生命周期
    # ----------------------------------------------------------

    def start(self) -> None:
        """启动调度器（幂等）。"""
        if self._scheduler.running:
            return
        self._scheduler.start()
        logger.info("[Scheduler] 任务调度器已启动")

    def shutdown(self) -> None:
        """关闭调度器（幂等）。"""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("[Scheduler] 任务调度器已关闭")

    @property
    def running(self) -> bool:
        return self._scheduler.running


_scheduler: Scheduler | None = None


def get_scheduler() -> Scheduler:
    """获取调度器单例。"""
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler


__all__ = ["Scheduler", "get_scheduler"]
