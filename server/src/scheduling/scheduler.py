#!/usr/bin/env python3
"""定时任务调度器（北辰 x-BeiChen）。

基于 APScheduler AsyncIOScheduler：
    - 注册周期性任务（如监控巡检：每 N 分钟触发一轮）
    - 与 FastAPI lifespan 联动：start() / shutdown()
默认不自动启动（由 main.py 按配置注册），避免骨架阶段空转。
"""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.core.config import settings
from src.core.logger import logger


class Scheduler:
    """应用级定时任务调度器（单例）。"""

    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
        self._jobs_registered = False

    def register_monitor_job(self, interval_minutes: int = 15) -> None:
        """注册数据监控巡检任务（周期性触发 monitor Agent）。"""
        from src.scheduling.jobs import monitor_scan_job

        if not self._scheduler.get_job("monitor_scan"):
            self._scheduler.add_job(
                monitor_scan_job,
                trigger="interval",
                minutes=interval_minutes,
                id="monitor_scan",
                name="数据监控巡检",
                replace_existing=True,
            )
            logger.info(f"[Scheduler] 注册监控巡检任务：每 {interval_minutes} 分钟")

    def register_customer_jobs(self, followup_interval_hours: int = 6, report_hour: str = "08:00") -> None:
        """注册客户管理 + 任务调度任务（跟进巡检 + 定时报表）。

        - followup 巡检：interval（默认每 6 小时一轮）
        - 日报：cron（默认每天 08:00）
        TODO(业务接入): 周报 cron（如每周一 09:00）按需追加。
        """
        from src.scheduling.jobs import customer_followup_job, customer_report_job

        if not self._scheduler.get_job("customer_followup"):
            self._scheduler.add_job(
                customer_followup_job,
                trigger="interval",
                hours=followup_interval_hours,
                id="customer_followup",
                name="客户跟进巡检",
                replace_existing=True,
            )
            logger.info(f"[Scheduler] 注册客户跟进巡检：每 {followup_interval_hours} 小时")
        if not self._scheduler.get_job("customer_report"):
            hour, minute = (int(x) for x in report_hour.split(":"))
            self._scheduler.add_job(
                customer_report_job,
                trigger="cron",
                hour=hour,
                minute=minute,
                id="customer_report",
                name="客户日报",
                kwargs={"report_type": "daily"},
                replace_existing=True,
            )
            logger.info(f"[Scheduler] 注册客户日报：每天 {report_hour}")

    def start(self) -> None:
        """启动调度器（幂等）。"""
        if self._scheduler.running:
            return
        self._scheduler.start()
        logger.info("[Scheduler] 定时任务调度器已启动")

    def shutdown(self) -> None:
        """关闭调度器（幂等）。"""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("[Scheduler] 定时任务调度器已关闭")

    @property
    def running(self) -> bool:
        return self._scheduler.running


_scheduler: Scheduler | None = None


def get_scheduler() -> Scheduler:
    """调度器单例。"""
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler


__all__ = ["Scheduler", "get_scheduler"]
