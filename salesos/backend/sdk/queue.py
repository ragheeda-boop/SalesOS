"""Task queue abstraction for background processing."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable

logger = logging.getLogger(__name__)


class TaskQueue(ABC):
    """Abstract task queue for background job processing."""

    @abstractmethod
    async def enqueue(
        self, task_name: str, payload: dict, delay_seconds: int = 0
    ) -> str:
        """Enqueue a task for background execution. Returns task ID."""

    @abstractmethod
    async def enqueue_unique(
        self, task_name: str, payload: dict, dedup_key: str
    ) -> str | None:
        """Enqueue only if no identical task is pending. Returns task ID or None."""


class RedisTaskQueue(TaskQueue):
    """Redis-backed task queue using simple list operations."""

    def __init__(self, redis):
        self._redis = redis
        self._prefix = "salesos:queue"

    async def enqueue(
        self, task_name: str, payload: dict, delay_seconds: int = 0
    ) -> str:
        import json
        import uuid

        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "name": task_name,
            "payload": payload,
            "attempts": 0,
            "max_attempts": 3,
        }
        queue_key = f"{self._prefix}:{task_name}"

        if delay_seconds > 0:
            await self._redis.zadd(
                f"{queue_key}:delayed",
                {json.dumps(task): delay_seconds},
            )
        else:
            await self._redis.rpush(queue_key, json.dumps(task))

        logger.info("Enqueued task %s: %s", task_id, task_name)
        return task_id

    async def enqueue_unique(
        self, task_name: str, payload: dict, dedup_key: str
    ) -> str | None:
        dedup_set_key = f"{self._prefix}:dedup:{task_name}"
        added = await self._redis.sadd(dedup_set_key, dedup_key)
        if added == 0:
            logger.debug("Duplicate task skipped: %s/%s", task_name, dedup_key)
            return None
        return await self.enqueue(task_name, payload)


class CeleryTaskQueue(TaskQueue):
    """Celery-backed task queue for production use."""

    def __init__(self, celery_app):
        self._celery = celery_app

    async def enqueue(
        self, task_name: str, payload: dict, delay_seconds: int = 0
    ) -> str:
        task = self._celery.send_task(
            task_name,
            kwargs=payload,
            countdown=delay_seconds,
        )
        return task.id

    async def enqueue_unique(
        self, task_name: str, payload: dict, dedup_key: str
    ) -> str | None:
        from celery.signals import task_received

        # Check if task with same dedup_key is already queued
        inspector = self._celery.control.inspect()
        scheduled = inspector.scheduled() or {}
        active = inspector.active() or {}

        for worker_tasks in {**scheduled, **active}.values():
            for t in worker_tasks:
                if t.get("kwargs", {}).get("dedup_key") == dedup_key:
                    return None

        return await self.enqueue(task_name, payload)
