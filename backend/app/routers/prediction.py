"""
Prediction Router for ML-based comment classification.

Endpoints:
- POST /api/predict - Batch predict comments (sync or async)
- POST /api/predict/single - Single comment prediction
- GET /api/predict/task/{task_id} - Get async task status

Requirements: 2.2, 2.3, 9.1
"""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionResponse,
)
from app.services.prediction_service import PredictionService, ModelLoadError

router = APIRouter(prefix="/api/predict", tags=["prediction"])

# In-memory task storage (will be replaced by Celery/Redis in Phase 4)
# This is a temporary solution for async mode until Celery is implemented
_task_store: dict[str, dict[str, Any]] = {}


@router.post("/", response_model=BatchPredictionResponse)
async def batch_predict(request: PredictionRequest) -> BatchPredictionResponse:
    """
    Batch predict comments for gambling content.
    
    Accepts a list of texts (1-1000 items) and returns predictions for each.
    Supports sync and async modes:
    - sync mode (default): Returns predictions immediately
    - async mode: Queues task and returns task_id for polling
    
    Requirements: 2.2, 2.3
    """
    try:
        prediction_service = PredictionService()
        
        if request.async_mode:
            # Async mode: Queue task and return task_id
            # Note: Full Celery integration will be implemented in Phase 4
            # For now, we process synchronously but return a task_id structure
            task_id = str(uuid.uuid4())
            
            # Process predictions
            results = prediction_service.predict_batch(request.texts)
            
            # Store results for later retrieval
            _task_store[task_id] = {
                "status": "completed",
                "results": results,
            }
            
            # Return with task_id (predictions included for immediate use)
            predictions = [
                PredictionResponse(
                    text=r["text"],
                    is_gambling=r["is_gambling"],
                    confidence=r["confidence"],
                )
                for r in results
            ]
            
            return BatchPredictionResponse(
                predictions=predictions,
                task_id=task_id,
            )
        else:
            # Sync mode: Process and return immediately
            results = prediction_service.predict_batch(request.texts)
            
            predictions = [
                PredictionResponse(
                    text=r["text"],
                    is_gambling=r["is_gambling"],
                    confidence=r["confidence"],
                )
                for r in results
            ]
            
            return BatchPredictionResponse(
                predictions=predictions,
                task_id=None,
            )
            
    except ModelLoadError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Model Unavailable",
                "error_code": "model_load_error",
                "message": str(e),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Prediction Error",
                "error_code": "prediction_error",
                "message": f"Failed to process predictions: {str(e)}",
            },
        )


@router.post("/single", response_model=PredictionResponse)
async def single_predict(text: str) -> PredictionResponse:
    """
    Predict whether a single comment is gambling-related.
    
    Args:
        text: The comment text to classify
        
    Returns:
        PredictionResponse with is_gambling boolean and confidence score
        
    Requirements: 2.2
    """
    try:
        prediction_service = PredictionService()
        result = prediction_service.predict_single(text)
        
        return PredictionResponse(
            text=result["text"],
            is_gambling=result["is_gambling"],
            confidence=result["confidence"],
        )
        
    except ModelLoadError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Model Unavailable",
                "error_code": "model_load_error",
                "message": str(e),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Prediction Error",
                "error_code": "prediction_error",
                "message": f"Failed to process prediction: {str(e)}",
            },
        )


@router.get("/task/{task_id}")
async def get_task_status(task_id: str) -> dict[str, Any]:
    """
    Get async task status and results.
    
    Returns the status of an async prediction task and its results
    if completed.
    
    Args:
        task_id: The task ID returned from async batch prediction
        
    Returns:
        Dictionary containing:
        - task_id: The task identifier
        - status: Task status (pending/processing/completed/failed)
        - results: Prediction results if completed
        
    Requirements: 9.1
    """
    # Check in-memory store first (temporary until Celery is implemented)
    if task_id in _task_store:
        task_data = _task_store[task_id]
        
        if task_data["status"] == "completed":
            predictions = [
                PredictionResponse(
                    text=r["text"],
                    is_gambling=r["is_gambling"],
                    confidence=r["confidence"],
                )
                for r in task_data["results"]
            ]
            
            return {
                "task_id": task_id,
                "status": "completed",
                "results": BatchPredictionResponse(
                    predictions=predictions,
                    task_id=task_id,
                ),
            }
        elif task_data["status"] == "failed":
            return {
                "task_id": task_id,
                "status": "failed",
                "error": task_data.get("error", "Unknown error"),
            }
        else:
            return {
                "task_id": task_id,
                "status": task_data["status"],
            }
    
    # Task not found
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "error": "Task Not Found",
            "error_code": "task_not_found",
            "message": f"Task with ID '{task_id}' not found",
        },
    )
