#!/usr/bin/env python3
"""定时任务定义（北辰 x-BeiChen）。

每个 job 是独立可测试的入口函数；与 Scheduler 解耦（job 不依赖调度器实例）。
"""

from __future__ import annotations

from typing import Any

from src.core.config import settings
from src.core.logger import logger


async def monitor_scan_job(account_ids: list[str] | None = None, **kwargs: Any) -> None:
    """数据监控巡检任务：触发一轮 monitor Agent 巡检。

    由 Scheduler 周期调用（也可手动触发）。
    TODO(业务接入): 账户清单从客户管理 Agent / 广告平台授权列表读取。
    """
    from src.infras.database import get_cached_database_provider
    from src.services.monitoring_service import MonitoringService

    if not settings.database.enabled:
        logger.warning("[Job] 数据库未启用（DATABASE_ENABLED=false），跳过监控巡检")
        return
    try:
        provider = get_cached_database_provider()
        with provider.session() as session:
            service = MonitoringService(session)
            task_ids = await service.trigger_scan(account_ids=account_ids)
            logger.info(f"[Job] 监控巡检完成，提交任务：{task_ids}")
    except Exception as exc:
        logger.exception(f"[Job] 监控巡检失败：{exc}")


__all__ = ["monitor_scan_job"]
