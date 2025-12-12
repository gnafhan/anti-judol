"""
Validation Router for user validation feedback operations.

Endpoints:
- POST /api/validation/submit - Submit single validation
- POST /api/validation/batch - Submit batch validation
- DELETE /api/validation/{id} - Undo validation (within time window)
- GET /api/validation/stats - Get validation statistics
- GET /api/validation/progress - Get progress toward retraining

Requirements: 1.2, 2.2, 7.2, 4.2
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.validation import (
    ValidationSubmit,
    BatchValidationSubmit,
    ValidationResponse,
    ValidationStats,
    BatchValidationResult,
)
from app.services.auth_service import get_current_user
from app.services.validation_service import (
    ValidationService,
    ValidationNotFoundError,
    ScanResultNotFoundError,
    UndoWindowExpiredError,
    ValidationError,
)

router = APIRouter(prefix="/api/validation", tags=["validation"])


@router.post("/submit", response_model=ValidationResponse, status_code=status.HTTP_201_CREATED)
async def submit_validation(
    request: ValidationSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ValidationResponse:
    """
    Submit a single validation for a scan result.
    
    Allows users to confirm or correct a prediction. If the prediction is correct,
    set is_correct=True. If incorrect, set is_correct=False and provide corrected_label.
    
    Requirements: 1.2
    """
    service = ValidationService(db)
    
    try:
        validation = await service.submit_validation(
            scan_result_id=request.scan_result_id,
            user_id=current_user.id,
            is_correct=request.is_correct,
            corrected_label=request.corrected_label,
        )
        
        return ValidationResponse(
            id=validation.id,
            scan_result_id=validation.scan_result_id,
            is_correction=validation.is_correction,
            corrected_label=validation.corrected_label,
            validated_at=validation.validated_at,
            can_undo=service._can_undo(validation.validated_at),
        )
        
    except ScanResultNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Scan Result Not Found",
                "error_code": "SCAN_RESULT_NOT_FOUND",
                "message": "Comment no longer exists",
            },
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Validation Error",
                "error_code": "VALIDATION_ERROR",
                "message": str(e),
            },
        )


@router.post("/batch", response_model=BatchValidationResult)
async def batch_validate(
    request: BatchValidationSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchValidationResult:
    """
    Submit batch validation for multiple scan results.
    
    Allows users to validate multiple comments at once with a single action:
    - confirm_all: Confirm all predictions as correct
    - mark_gambling: Mark all as gambling
    - mark_clean: Mark all as clean
    
    Requirements: 2.2
    """
    service = ValidationService(db)
    
    result = await service.batch_validate(
        result_ids=request.result_ids,
        user_id=current_user.id,
        action=request.action,
    )
    
    return result


@router.delete("/{validation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def undo_validation(
    validation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Undo a validation within the time window (5 seconds).
    
    Deletes the validation record and restores the scan result to its
    pre-validation state. Only works within the undo window.
    
    Requirements: 7.2
    """
    service = ValidationService(db)
    
    try:
        await service.undo_validation(
            validation_id=validation_id,
            user_id=current_user.id,
        )
    except ValidationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Validation Not Found",
                "error_code": "VALIDATION_NOT_FOUND",
                "message": f"Validation with ID '{validation_id}' not found",
            },
        )
    except UndoWindowExpiredError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Undo Window Expired",
                "error_code": "UNDO_EXPIRED",
                "message": "Undo window expired (5 seconds)",
            },
        )


@router.get("/stats", response_model=ValidationStats)
async def get_validation_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ValidationStats:
    """
    Get validation statistics for the current user.
    
    Returns cumulative statistics including total validated, corrections made,
    and progress toward the retraining threshold.
    
    Requirements: 4.2
    """
    service = ValidationService(db)
    
    stats = await service.get_validation_stats(user_id=current_user.id)
    
    return stats


@router.get("/progress", response_model=ValidationStats)
async def get_validation_progress(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ValidationStats:
    """
    Get progress toward retraining threshold.
    
    Returns global validation statistics showing progress toward
    the automatic model retraining threshold.
    
    Requirements: 4.2
    """
    service = ValidationService(db)
    
    # Get global stats (not filtered by user)
    stats = await service.get_validation_stats(user_id=None)
    
    return stats


@router.get("/scan/{scan_id}", response_model=list[ValidationResponse])
async def get_validations_for_scan(
    scan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ValidationResponse]:
    """
    Get all validations for a specific scan.
    
    Returns all validation records for scan results belonging to the given scan,
    filtered by the current user.
    """
    service = ValidationService(db)
    
    validations = await service.get_validations_for_scan(
        scan_id=scan_id,
        user_id=current_user.id,
    )
    
    return [
        ValidationResponse(
            id=v.id,
            scan_result_id=v.scan_result_id,
            is_correction=v.is_correction,
            corrected_label=v.corrected_label,
            validated_at=v.validated_at,
            can_undo=service._can_undo(v.validated_at),
        )
        for v in validations
    ]
