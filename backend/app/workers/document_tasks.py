from celery import Task
from app.workers.celery_app import celery_app


class _DocumentTask(Task):
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        import logging
        logging.getLogger(__name__).error(
            "Task %s failed: %s", task_id, exc, exc_info=einfo
        )


@celery_app.task(
    bind=True,
    base=_DocumentTask,
    name="app.workers.document_tasks.process_document",
    queue="documents",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def process_document(self, document_id: str) -> None:
    from app.ingestion.pipeline import run_pipeline

    try:
        run_pipeline(document_id)
    except Exception as exc:
        raise self.retry(exc=exc)
