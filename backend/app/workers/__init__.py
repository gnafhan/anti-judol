"""
Celery Workers and Tasks module.
Exports the Celery app instance and tasks for use by workers and the main application.
"""

from app.workers.celery_app import celery_app
from app.workers.tasks import (
    scan_video_comments,
    batch_predict,
    cleanup_old_results,
)

__all__ = [
    "celery_app",
    "scan_video_comments",
    "batch_predict",
    "cleanup_old_results",
]
