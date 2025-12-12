"""
Model Management Router for admin operations on ML models.

Endpoints:
- GET /api/model/versions - List model versions
- GET /api/model/current - Get current active model info
- POST /api/model/retrain - Manually trigger retraining
- POST /api/model/rollback/{version_id} - Rollback to previous version
- GET /api/model/metrics - Get model performance metrics

Requirements: 5.3, 10.1
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.retraining_service import (
    RetrainingService,
    RetrainingError,
    InsufficientDataError,
    ModelDeploymentError,
)

settings = get_settings()

router = APIRouter(prefix="/api/model", tags=["model"])


# Response schemas
class ModelVersionResponse(BaseModel):
    """Response schema for model version information."""
    id: UUID
    version: str
    accuracy: float | None
    precision_score: float | None
    recall_score: float | None
    f1_score: float | None
    is_active: bool
    training_samples: int
    validation_samples: int
    created_at: str
    activated_at: str | None
    deactivated_at: str | None

    class Config:
        from_attributes = True


class ModelMetricsResponse(BaseModel):
    """Response schema for model metrics."""
    current_version: str | None
    accuracy: float | None
    precision: float | None
    recall: float | None
    f1: float | None
    training_samples: int | None
    validation_samples: int | None
    total_versions: int
    pending_validations: int


class MetricsTrendPoint(BaseModel):
    """Single point in metrics trend."""
    version: str
    accuracy: float | None
    precision: float | None
    recall: float | None
    f1: float | None
    created_at: str


class MetricsTrendResponse(BaseModel):
    """Response schema for metrics trend over model versions."""
    trend: list[MetricsTrendPoint]
    improvement_summary: dict


class RetrainingProgressResponse(BaseModel):
    """Response schema for retraining progress."""
    is_training: bool
    current_step: str | None
    progress_percent: float
    started_at: str | None
    estimated_completion: str | None
    error_message: str | None


class RetrainingResponse(BaseModel):
    """Response schema for retraining operation."""
    success: bool
    message: str
    model_version: ModelVersionResponse | None = None
    metrics: dict | None = None


class RollbackResponse(BaseModel):
    """Response schema for rollback operation."""
    success: bool
    message: str
    model_version: ModelVersionResponse | None = None


class RetrainingPreviewResponse(BaseModel):
    """Response schema for retraining preview/summary."""
    original_dataset_samples: int
    total_validations: int  # All validations (used + unused)
    pending_validations: int  # Only new/unused validations
    total_samples_after_training: int
    corrections_count: int
    confirmations_count: int
    current_model_version: str | None
    current_model_accuracy: float | None
    can_retrain: bool
    message: str | None


# Admin authentication dependency
async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency that ensures the current user is an admin.
    
    Checks if the user's email is in the admin_emails configuration.
    
    Raises:
        HTTPException 403: If user is not an admin
    """
    admin_emails = settings.admin_email_list
    
    # If no admin emails configured, allow all authenticated users (for development)
    if not admin_emails:
        return current_user
    
    if current_user.email not in admin_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "error_code": "ADMIN_REQUIRED",
                "message": "Admin access required for this operation",
            },
        )
    
    return current_user


def _model_to_response(model) -> ModelVersionResponse:
    """Convert ModelVersion to response schema."""
    return ModelVersionResponse(
        id=model.id,
        version=model.version,
        accuracy=model.accuracy,
        precision_score=model.precision_score,
        recall_score=model.recall_score,
        f1_score=model.f1_score,
        is_active=model.is_active,
        training_samples=model.training_samples,
        validation_samples=model.validation_samples,
        created_at=model.created_at.isoformat() if model.created_at else None,
        activated_at=model.activated_at.isoformat() if model.activated_at else None,
        deactivated_at=model.deactivated_at.isoformat() if model.deactivated_at else None,
    )


@router.get("/versions", response_model=list[ModelVersionResponse])
async def get_model_versions(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
) -> list[ModelVersionResponse]:
    """
    List model versions ordered by creation date (newest first).
    
    Admin-only endpoint.
    
    Requirements: 5.3
    """
    service = RetrainingService(db)
    versions = await service.get_model_versions(limit=limit)
    
    return [_model_to_response(v) for v in versions]


@router.get("/current", response_model=ModelVersionResponse | None)
async def get_current_model(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
) -> ModelVersionResponse | None:
    """
    Get the currently active model version.
    
    Admin-only endpoint.
    
    Requirements: 5.3
    """
    service = RetrainingService(db)
    active_model = await service.get_active_model()
    
    if active_model is None:
        return None
    
    return _model_to_response(active_model)


@router.get("/retrain/preview", response_model=RetrainingPreviewResponse)
async def get_retraining_preview(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
) -> RetrainingPreviewResponse:
    """
    Get preview of retraining data before starting.
    
    Returns summary of data that will be used for retraining.
    Admin-only endpoint.
    """
    service = RetrainingService(db)
    
    # Get current model
    active_model = await service.get_active_model()
    
    # Get validation counts - now we use ALL validations for training
    total_validations = await service.get_total_validation_count()
    pending_count = await service.get_unused_validation_count()
    corrections_count, confirmations_count = await service.get_validation_breakdown()
    
    # Get original dataset size
    original_size = await service.get_original_dataset_size()
    
    # Total samples = original + ALL validations (dataset always grows)
    total_samples = original_size + total_validations
    min_samples = getattr(settings, 'min_training_samples', 100)
    can_retrain = total_samples >= min_samples
    
    message = None
    if not can_retrain:
        message = f"Insufficient data. Need at least {min_samples} samples, have {total_samples}."
    elif pending_count == 0:
        message = "No new validations. Model will be retrained with all existing data."
    
    return RetrainingPreviewResponse(
        original_dataset_samples=original_size,
        total_validations=total_validations,
        pending_validations=pending_count,
        total_samples_after_training=total_samples,
        corrections_count=corrections_count,
        confirmations_count=confirmations_count,
        current_model_version=active_model.version if active_model else None,
        current_model_accuracy=active_model.accuracy if active_model else None,
        can_retrain=can_retrain,
        message=message,
    )


class RetrainingStartResponse(BaseModel):
    """Response schema for starting retraining (async)."""
    success: bool
    message: str
    task_id: str | None = None


@router.post("/retrain", response_model=RetrainingStartResponse)
async def trigger_retraining(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
) -> RetrainingStartResponse:
    """
    Manually trigger model retraining (async via Celery).
    
    Starts a background task to combine original dataset with validation 
    feedback and train a new model. The current model continues serving
    predictions during retraining.
    
    Admin-only endpoint.
    
    Requirements: 5.3, 10.1
    """
    from app.workers.tasks import retrain_model
    
    service = RetrainingService(db)
    
    # Check if we have enough data before starting the task
    try:
        pending_count = await service.get_unused_validation_count()
        original_size = await service.get_original_dataset_size()
        total_samples = original_size + pending_count
        min_samples = getattr(settings, 'min_training_samples', 100)
        
        if total_samples < min_samples:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Insufficient Data",
                    "error_code": "INSUFFICIENT_DATA",
                    "message": f"Insufficient training data: {total_samples} samples (minimum: {min_samples})",
                },
            )
        
        # Start the Celery task
        task = retrain_model.delay(triggered_by="manual")
        
        return RetrainingStartResponse(
            success=True,
            message=f"Retraining started. Task ID: {task.id}. Training will run in background.",
            task_id=task.id,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Retraining Error",
                "error_code": "RETRAINING_ERROR",
                "message": str(e),
            },
        )


@router.post("/rollback/{version_id}", response_model=RollbackResponse)
async def rollback_model(
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
) -> RollbackResponse:
    """
    Rollback to a previous model version.
    
    Deactivates the current model and activates the specified version.
    Reloads the prediction service with the rolled-back model.
    Admin-only endpoint.
    
    Requirements: 5.3
    """
    from pathlib import Path
    from app.services.prediction_service import PredictionService
    
    service = RetrainingService(db)
    
    try:
        model_version = await service.rollback_model(version_id)
        
        # Reload prediction service with the rolled-back model
        model_path = Path(model_version.file_path)
        reload_success = PredictionService.reload_model(model_path)
        
        if reload_success:
            return RollbackResponse(
                success=True,
                message=f"Rolled back to model version: {model_version.version}",
                model_version=_model_to_response(model_version),
            )
        else:
            # Rollback succeeded but model reload failed - still return success
            # as the database state is correct
            return RollbackResponse(
                success=True,
                message=f"Rolled back to model version: {model_version.version}. Note: Model hot-swap pending, may require service restart.",
                model_version=_model_to_response(model_version),
            )
        
    except RetrainingError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Rollback Error",
                "error_code": "ROLLBACK_ERROR",
                "message": str(e),
            },
        )


@router.get("/metrics", response_model=ModelMetricsResponse)
async def get_model_metrics(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
) -> ModelMetricsResponse:
    """
    Get model performance metrics and statistics.
    
    Returns current model metrics, total versions, and pending validations.
    Admin-only endpoint.
    
    Requirements: 10.1
    """
    service = RetrainingService(db)
    
    # Get active model
    active_model = await service.get_active_model()
    
    # Get all versions count
    versions = await service.get_model_versions(limit=1000)
    total_versions = len(versions)
    
    # Get pending validations count
    pending_validations = await service.get_unused_validation_count()
    
    if active_model:
        return ModelMetricsResponse(
            current_version=active_model.version,
            accuracy=active_model.accuracy,
            precision=active_model.precision_score,
            recall=active_model.recall_score,
            f1=active_model.f1_score,
            training_samples=active_model.training_samples,
            validation_samples=active_model.validation_samples,
            total_versions=total_versions,
            pending_validations=pending_validations,
        )
    
    return ModelMetricsResponse(
        current_version=None,
        accuracy=None,
        precision=None,
        recall=None,
        f1=None,
        training_samples=None,
        validation_samples=None,
        total_versions=total_versions,
        pending_validations=pending_validations,
    )


@router.get("/metrics/trend", response_model=MetricsTrendResponse)
async def get_metrics_trend(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
) -> MetricsTrendResponse:
    """
    Get metrics trend over model versions.
    
    Returns historical metrics for visualization and improvement summary.
    Admin-only endpoint.
    """
    service = RetrainingService(db)
    
    # Get model versions ordered by creation date (oldest first for trend)
    versions = await service.get_model_versions(limit=limit)
    versions_reversed = list(reversed(versions))  # Oldest first
    
    trend = [
        MetricsTrendPoint(
            version=v.version,
            accuracy=v.accuracy,
            precision=v.precision_score,
            recall=v.recall_score,
            f1=v.f1_score,
            created_at=v.created_at.isoformat() if v.created_at else None,
        )
        for v in versions_reversed
    ]
    
    # Calculate improvement summary
    improvement_summary = {}
    if len(versions_reversed) >= 2:
        first = versions_reversed[0]
        last = versions_reversed[-1]
        
        if first.accuracy is not None and last.accuracy is not None:
            improvement_summary["accuracy_change"] = last.accuracy - first.accuracy
            improvement_summary["accuracy_percent"] = (
                ((last.accuracy - first.accuracy) / first.accuracy * 100)
                if first.accuracy > 0 else 0
            )
        
        if first.f1_score is not None and last.f1_score is not None:
            improvement_summary["f1_change"] = last.f1_score - first.f1_score
            improvement_summary["f1_percent"] = (
                ((last.f1_score - first.f1_score) / first.f1_score * 100)
                if first.f1_score > 0 else 0
            )
    
    return MetricsTrendResponse(
        trend=trend,
        improvement_summary=improvement_summary,
    )


@router.get("/training/progress", response_model=RetrainingProgressResponse)
async def get_training_progress(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
) -> RetrainingProgressResponse:
    """
    Get current retraining progress.
    
    Returns training status, current step, and progress percentage.
    Admin-only endpoint.
    """
    service = RetrainingService(db)
    
    # Check if training is in progress
    training_status = await service.get_training_status()
    
    return RetrainingProgressResponse(
        is_training=training_status.get("is_training", False),
        current_step=training_status.get("current_step"),
        progress_percent=training_status.get("progress_percent", 0),
        started_at=training_status.get("started_at"),
        estimated_completion=training_status.get("estimated_completion"),
        error_message=training_status.get("error_message"),
    )


class TaskStatusResponse(BaseModel):
    """Response schema for Celery task status."""
    task_id: str
    status: str
    progress: int | None = None
    stage: str | None = None
    message: str | None = None
    result: dict | None = None


@router.get("/training/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    _admin: User = Depends(get_admin_user),
) -> TaskStatusResponse:
    """
    Get status of a specific retraining task.
    
    Returns task status, progress, and result if completed.
    Admin-only endpoint.
    """
    from celery.result import AsyncResult
    from app.workers.celery_app import celery_app
    
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = TaskStatusResponse(
        task_id=task_id,
        status=task_result.status,
    )
    
    if task_result.status == 'PROGRESS':
        meta = task_result.info or {}
        response.progress = meta.get('progress', 0)
        response.stage = meta.get('stage')
        response.message = meta.get('message')
    elif task_result.status == 'SUCCESS':
        response.progress = 100
        response.stage = 'completed'
        response.result = task_result.result
        response.message = 'Retraining completed successfully'
    elif task_result.status == 'FAILURE':
        response.progress = 0
        response.stage = 'failed'
        response.message = str(task_result.result) if task_result.result else 'Task failed'
    elif task_result.status == 'PENDING':
        response.progress = 0
        response.stage = 'pending'
        response.message = 'Task is waiting to be processed'
    elif task_result.status == 'STARTED':
        response.progress = 5
        response.stage = 'started'
        response.message = 'Task has started processing'
    elif task_result.status == 'RETRY':
        meta = task_result.info or {}
        response.progress = meta.get('progress', 0)
        response.stage = 'retry'
        response.message = 'Task is being retried'
    
    return response
