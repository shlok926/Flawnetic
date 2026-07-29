from celery import Celery
from config.settings import settings

celery_app = Celery(
    "flawnetic",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["workers.tasks"]  # will be populated in Phase 1
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
)
