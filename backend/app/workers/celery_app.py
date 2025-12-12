"""
Celery application configuration.
Configures broker, backend, task queues, rate limits, and retry policies.

Requirements: 9.1, 9.3, 12.1, 12.2
"""

from celery import Celery
from kombu import Queue, Exchange

from app.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "gambling_comment_detector",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Define exchanges
default_exchange = Exchange("default", type="direct")
predictions_exchange = Exchange("predictions", type="direct")
youtube_exchange = Exchange("youtube", type="direct")
retraining_exchange = Exchange("retraining", type="direct")

# Configure Celery
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task queues configuration
    task_queues=(
        Queue("default", default_exchange, routing_key="default"),
        Queue("predictions", predictions_exchange, routing_key="predictions"),
        Queue("youtube", youtube_exchange, routing_key="youtube"),
        Queue("retraining", retraining_exchange, routing_key="retraining"),
    ),
    
    # Default queue
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    
    # Task routing
    task_routes={
        "app.workers.tasks.batch_predict": {"queue": "predictions"},
        "app.workers.tasks.scan_video_comments": {"queue": "youtube"},
        "app.workers.tasks.cleanup_old_results": {"queue": "default"},
        "app.workers.tasks.retrain_model": {"queue": "retraining"},
    },
    
    # Rate limits (Requirements 12.1, 12.2)
    # Scan operations: 10 requests per minute
    # Prediction operations: 30 requests per minute
    task_annotations={
        "app.workers.tasks.scan_video_comments": {
            "rate_limit": f"{settings.scan_rate_limit_per_minute}/m",
        },
        "app.workers.tasks.batch_predict": {
            "rate_limit": f"{settings.prediction_rate_limit_per_minute}/m",
        },
    },
    
    # Retry policy (Requirements 9.3, 9.4)
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Default retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Process one task at a time for rate limiting
    worker_concurrency=4,  # Number of concurrent workers
    
    # Task execution settings
    task_time_limit=1800,  # 30 minutes hard limit (for retraining)
    task_soft_time_limit=1740,  # 29 minutes soft limit
    
    # Task tracking
    task_track_started=True,
    task_send_sent_event=True,
)


# Celery Beat schedule for periodic tasks (Requirement 9.5)
celery_app.conf.beat_schedule = {
    "cleanup-old-results-daily": {
        "task": "app.workers.tasks.cleanup_old_results",
        "schedule": 86400.0,  # Run once per day (24 hours in seconds)
        "options": {"queue": "default"},
    },
}

# Beat scheduler settings
celery_app.conf.beat_scheduler = "celery.beat:PersistentScheduler"
celery_app.conf.beat_schedule_filename = "celerybeat-schedule"
