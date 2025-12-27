"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "thegitleague",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.sync_tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,  # One task at a time per worker
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (memory cleanup)
)

# Celery Beat schedule (periodic tasks)
celery_app.conf.beat_schedule = {
    # Example: sync all repos every 6 hours
    # This will be configured per-repo in the database
    "cleanup-old-magic-links": {
        "task": "app.workers.sync_tasks.cleanup_old_magic_links",
        "schedule": crontab(minute=0, hour="*/1"),  # Every hour
    },
}


if __name__ == "__main__":
    celery_app.start()
