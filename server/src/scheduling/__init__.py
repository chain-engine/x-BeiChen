"""任务调度层（北辰 x-BeiChen）。

- scheduler.py:  通用调度器（APScheduler AsyncIOScheduler 单例，只提供注册原语）
- bootstrap.py: 默认任务装配（业务 job 函数引用 + trigger 参数在此注入）
- jobs.py:       业务任务钩子（独立可测试，被 bootstrap 引用）
"""

from src.scheduling.scheduler import Scheduler, get_scheduler

__all__ = ["Scheduler", "get_scheduler"]
