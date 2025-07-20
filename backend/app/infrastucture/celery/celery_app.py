from celery import Celery
from decouple import config
from app.infrastucture.logs.logger import default_logger

# Celery configuration
CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="amqp://admin:admin123@rabbitmq:5672//")
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="rpc://")

# Create Celery app
celery_app = Celery(
    "oms_backend",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.infrastucture.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
)

# Log Celery startup
default_logger.info("Celery app configured", broker_url=CELERY_BROKER_URL)

if __name__ == "__main__":
    celery_app.start() 