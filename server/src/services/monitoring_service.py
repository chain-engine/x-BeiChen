#!/usr/bin/env python3
"""监控业务服务（北辰 x-BeiChen）。

提供监控域的业务入口：
    - 巡检触发：调度器调用（按账户批量提交监控任务）
    - 告警查询：管理后台告警面板数据（事件表聚合）
业务规则在此层，数据访问走 repositories，不读取 Request。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from src.constants import AgentType
from src.core.logger import logger
from src.services.agent_task_service import AgentTaskService


class MonitoringService:
    """数据监控业务服务。"""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._task_service = AgentTaskService(session)

    async def trigger_scan(self, account_ids: list[str] | None = None) -> list[int]:
        """触发一轮数据监控巡检：对每个账户提交一个 monitor 任务。

        TODO(业务接入): 账户清单从客户管理 Agent / 广告平台授权列表读取。
        """
        targets = account_ids or ["acc_default"]
        task_ids: list[int] = []
        for account_id in targets:
            task = await self._task_service.submit_task(
                task_type=str(AgentType.MONITOR),
                payload={"account_id": account_id},
            )
            task_ids.append(task.id)
            logger.info(f"[MonitoringService] 巡检任务已提交：id={task.id} account={account_id}")
        return task_ids

    def list_alerts(self, page: int = 1, page_size: int = 20) -> tuple[list[Any], int]:
        """查询告警事件（管理后台告警面板）。

        口径：EventType.ALERT_RAISED（monitor 子图告警分支发布的即时告警事件；
        SUGGESTION_CREATED 为建议单事件，走审批闸门，不属于告警面板）。
        """
        return self._task_service.list_events(event_type="alert_raised", page=page, page_size=page_size)
