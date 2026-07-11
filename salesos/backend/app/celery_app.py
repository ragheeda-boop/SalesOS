"""Celery application configuration for background task processing."""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "salesos",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.celery_task_time_limit,
    task_soft_time_limit=settings.celery_task_soft_time_limit,
    worker_max_tasks_per_child=settings.celery_worker_max_tasks_per_child,
    task_acks_late=True,
    worker_prefetch_multiplier=settings.celery_worker_prefetch_multiplier,
    result_expires=settings.celery_result_expires,
)
