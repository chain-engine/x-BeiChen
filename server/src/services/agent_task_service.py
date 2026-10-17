#!/usr/bin/env python3
"""Agent 任务服务（北辰 x-BeiChen 业务层）。

职责边界（api → services → repositories 单向）：
    - 任务提交：落库（pending）→ 调 AgentRuntime 派发执行 → 回写状态/结果 → 事件落库
    - 任务查询：列表 / 详情（管理后台）
    - 人工接管：interrupt 断点 → resume 恢复 → 回写人工决策
    - 事件查询：协作事件分页（审计面板）
    - 不读取 Request 对象；HTTP 参数由 api 层解析后传入

说明：真正的"编排执行"在 AgentRuntime（图编译 / invoke / resume），
本服务是任务门面：负责任务生命周期管理（提交、恢复、查询），不承载图编排。
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from src.agents.runtime import AgentRuntime, get_agent_runtime
from src.constants import TaskStatus
from src.core.config import settings
from src.core.exceptions import NotFoundException, ValidationException
from src.core.logger import logger
from src.infras.event_bus import EventBus, get_event_bus
from src.models.entities.agent_event import AgentEvent
from src.models.entities.agent_task import AgentTask
from src.repositories.agent_event_repository import AgentEventRepository
from src.repositories.agent_task_repository import AgentTaskRepository


class AgentTaskService:
    """Agent 任务服务：任务全生命周期管理（提交 / 恢复 / 查询 / 事件查询）。

    依赖（runtime / event_bus）通过构造函数注入，默认走进程级工厂单例；
    测试或多实现切换时可传入 Mock/替身，不再硬绑全局状态。
    """

    def __init__(
        self,
        session: Session,
        runtime: AgentRuntime | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._session = session
        self._task_repo = AgentTaskRepository(session)
        self._event_repo = AgentEventRepository(session)
        self._runtime: AgentRuntime = runtime or get_agent_runtime()
        self._event_bus: EventBus = event_bus or get_event_bus()

    # ----------------------------------------------------------
    # 任务提交
    # ----------------------------------------------------------

    async def submit_task(
        self,
        task_type: str,
        payload: dict[str, Any],
        timeout_at: datetime | None = None,
    ) -> AgentTask:
        """提交一个 Agent 任务并同步执行（骨架阶段同步；二期改异步队列）。

        Args:
            task_type: 任务类型（AgentType.mark，如 "monitor"）
            payload: 任务入参（由各 Agent 自定义结构，已注册 Agent 的 payload 字段枚举）：
                monitor（数据监控）:
                    account_id: str，可选，默认 "acc_default"（广告账户 ID）
                    campaign_id: str，可选（广告计划 ID，缺省查账户汇总）
                business_chat（商务对话）:
                    message: str，必填（用户消息文本，用于意图识别）
                    customer_id: str，可选（客户 ID，事件关联用）
                customer（客户管理+任务调度）:
                    scope: str，可选，默认 "due_followup"；取值 full（全量）/
                        due_followup（跟进到期）/ by_ids（指定客户）/ report（触发报表任务）
                    customer_ids: list[str]，scope=by_ids 时必填
                    report_type: str，scope=report 时可选，daily/weekly（当前编排固定产出日报）
            timeout_at: 超时时间点（缺省按配置 agent.task_timeout_seconds）

        Returns:
            回写执行结果后的 AgentTask（含 thread_id / status / result）

        事件双写契约：编排产生的事件同时「落库留痕 + publish 事件总线」，
        publish 失败不影响主流程（仅记日志），总线作为 Agent 间协作广播通道。
        """
        # 1. 校验任务类型可路由（提前失败，避免无效任务落库）
        from src.agents.registry import agent_registry

        if not agent_registry.has(task_type):
            raise ValidationException(f"任务类型未注册 Agent：{task_type}")

        # 2. 落库 pending（先持久化，获取任务 ID 作为审计主键）
        task = AgentTask(
            task_type=task_type,
            payload=payload,
            status=TaskStatus.PENDING,
            max_retries=settings.agent.task_max_retries,
            timeout_at=timeout_at
            or datetime.now(UTC) + timedelta(seconds=settings.agent.task_timeout_seconds),
        )
        self._task_repo.add(task)
        self._task_repo.commit()
        logger.info(f"[TaskService] 任务已落库：id={task.id} type={task_type}")

        # 3. 派发执行（同步 LangGraph invoke 放线程池，避免阻塞事件循环；
        #    invoke 内部不触碰请求级 SQLAlchemy session，线程安全）
        thread_id = f"task:{task.id}"
        loop = asyncio.get_running_loop()
        final_state = await loop.run_in_executor(
            None,
            lambda: self._runtime.invoke_task(
                task_type=task_type,
                payload=payload,
                thread_id=thread_id,
                task_id=task.id,
            ),
        )

        # 4. 回写执行结果
        self._apply_final_state(task, final_state, thread_id)

        # 5. 事件双写：落库留痕 + 发布事件总线（Agent 协作广播）
        await self._persist_and_publish_events(final_state)

        self._task_repo.commit()
        return task

    async def _persist_and_publish_events(self, final_state: dict[str, Any]) -> None:
        """事件双写：agent_events 落库 + EventBus publish（失败仅记日志不阻断）。"""
        from src.infras.event_bus import EventMessage

        for event in final_state.get("events", []):
            self._event_repo.add(
                AgentEvent(
                    event_type=event.get("type", "unknown"),
                    source_agent=event.get("source"),
                    target_agent=event.get("target"),
                    payload=event.get("payload"),
                    status="recorded",
                )
            )
            try:
                await self._event_bus.publish(
                    EventMessage(
                        event_type=event.get("type", "unknown"),
                        payload=event.get("payload") or {},
                        source_agent=event.get("source"),
                        target_agent=event.get("target"),
                    )
                )
            except Exception as exc:
                logger.exception(f"[TaskService] 事件发布失败（已落库留痕）：{exc}")

    def _apply_final_state(self, task: AgentTask, final_state: dict[str, Any], thread_id: str) -> None:
        """把编排图最终状态回写到任务实体。"""
        task.thread_id = thread_id
        task.status = final_state.get("status", TaskStatus.SUCCESS)
        task.assignee_agent = final_state.get("target_agent")  # 路由结果回写（②③④：Agent 归属可查）
        task.result = final_state.get("result") or final_state
        task.error_message = final_state.get("error")
        task.approval_no = final_state.get("approval_no")
        task.timeout_at = None
        if final_state.get("status") == TaskStatus.FAILED.mark:
            task.retry_count += 1
        logger.info(f"[TaskService] 任务结束：id={task.id} status={task.status} assignee={task.assignee_agent}")

    # ----------------------------------------------------------
    # 任务查询
    # ----------------------------------------------------------

    def get_task(self, task_id: int) -> AgentTask:
        task = self._task_repo.get(task_id)
        if task is None:
            raise NotFoundException(f"任务不存在：{task_id}")
        return task

    def list_tasks(self, status: str | None = None, task_type: str | None = None, page: int = 1, page_size: int = 20) -> tuple[list[AgentTask], int]:
        offset = (page - 1) * page_size
        if status:
            items = self._task_repo.list_by_status(status, offset=offset, limit=page_size)
            total = self._task_repo.count_by_status(status)
        elif task_type:
            items = self._task_repo.list_by_task_type(task_type, offset=offset, limit=page_size)
            total = self._task_repo.count(AgentTask.task_type == task_type)
        else:
            items = self._task_repo.list(order_by=self._task_repo.model_class.id.desc(), offset=offset, limit=page_size)
            total = self._task_repo.count()
        return items, total

    # ----------------------------------------------------------
    # 人工接管（interrupt → resume）
    # ----------------------------------------------------------

    async def resume_task(self, task_id: int, decision: str, remark: str | None = None, extra: dict[str, Any] | None = None) -> AgentTask:
        """恢复被 interrupt 暂停的任务（人工决策 approve/reject/adjust）。

        恢复后同样执行事件双写（人工决策产生的后续事件落库 + 广播）。
        """
        task = self.get_task(task_id)
        if not task.thread_id:
            raise ValidationException("任务无线程 ID，无法恢复（可能未执行或已完成）")
        update = {"decision": decision, "remark": remark, "extra": extra or {}}
        loop = asyncio.get_running_loop()
        final_state = await loop.run_in_executor(
            None,
            lambda: self._runtime.resume_task(task.thread_id, update),
        )
        self._apply_final_state(task, final_state, task.thread_id)
        await self._persist_and_publish_events(final_state)
        self._task_repo.commit()
        return task

    # ----------------------------------------------------------
    # 事件查询
    # ----------------------------------------------------------

    def list_events(self, event_type: str | None = None, page: int = 1, page_size: int = 20) -> tuple[list[AgentEvent], int]:
        offset = (page - 1) * page_size
        if event_type:
            items = self._event_repo.list_by_type(event_type, offset=offset, limit=page_size)
            total = self._event_repo.count(AgentEvent.event_type == event_type)
        else:
            items = self._event_repo.list_recent(offset=offset, limit=page_size)
            total = self._event_repo.count()
        return items, total
