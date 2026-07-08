"""Celery application configuration for background task processing."""

import os

from celery import Celery

celery_app = Celery(
    "salesos",
    broker=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
    backend=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,
    task_soft_time_limit=300,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600 * 24,
)
