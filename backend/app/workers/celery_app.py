from celery import Celery
from app.config import settings

celery_app = Celery(
    "docmind",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.document_tasks", "app.workers.maintenance_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.document_tasks.*": {"queue": "documents"},
        "app.workers.maintenance_tasks.*": {"queue": "documents"},
    },
    beat_schedule={
        "cleanup-stale-docs": {
            "task": "app.workers.maintenance_tasks.cleanup_stale_documents",
            "schedule": 900,  # every 15 min
        },
        "retry-failed-docs": {
            "task": "app.workers.maintenance_tasks.retry_failed_documents",
            "schedule": 1800,  # every 30 min
        },
    },
)
