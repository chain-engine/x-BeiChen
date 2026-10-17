#!/usr/bin/env python3
"""默认任务装配（北辰 x-BeiChen）。

业务触发配置集中在此：把具体 job 函数引用 + trigger 参数注入通用 Scheduler。
Scheduler 本身不感知业务，新增 / 调整任务只改本文件，不动调度器类。

当前装配：
    - monitor_scan      interval 每 15 分钟   数据监控巡检
    - customer_followup interval 每 6 小时   客户跟进巡检
    - customer_report   cron 每天 08:00      客户日报
"""

from __future__ import annotations

from src.scheduling.jobs import (
    customer_followup_job,
    customer_report_job,
    monitor_scan_job,
)
from src.scheduling.scheduler import Scheduler


def register_default_jobs(scheduler: Scheduler) -> None:
    """把默认业务 job 绑定进调度器（幂等，去重由通用原语保证）。

    Args:
        scheduler: 通用调度器实例（通常为 get_scheduler() 单例）
    """
    # 数据监控巡检：每 15 分钟一轮（interval 周期）
    scheduler.add_interval(
        monitor_scan_job,
        job_id="monitor_scan",
        name="数据监控巡检",
        minutes=15,
    )
    # 客户跟进巡检：每 6 小时一轮（interval 周期）
    scheduler.add_interval(
        customer_followup_job,
        job_id="customer_followup",
        name="客户跟进巡检",
        hours=6,
    )
    # 客户日报：每天 08:00（cron 定点）
    scheduler.add_cron(
        customer_report_job,
        job_id="customer_report",
        name="客户日报",
        hour=8,
        minute=0,
        kwargs={"report_type": "daily"},
    )


__all__ = ["register_default_jobs"]
