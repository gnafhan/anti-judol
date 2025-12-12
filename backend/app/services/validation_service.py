"""
Validation service for handling user validation feedback operations.

This service provides:
- Single and batch validation submission
- Undo validation within time window
- Validation statistics
- Retraining threshold checking

Requirements: 1.2, 2.3, 7.2, 4.2, 5.1
"""

from datetime import datetime, timezone, timedelta
from typing import Literal
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.validation import ValidationFeedback
from app.models.scan import ScanResult
from app.schemas.validation import (
    ValidationResponse,
    ValidationStats,
    BatchValidationResult,
)

settings = get_settings()

# Undo window in seconds (Requirement 7.2, 7.3)
UNDO_WINDOW_SECONDS = 5

# Default retraining threshold (Requirement 5.1)
DEFAULT_RETRAINING_THRESHOLD = 100


class ValidationError(Exception):
    """Base exception for validation errors."""
    pass


class ValidationNotFoundError(ValidationError):
    """Raised when validation record is not found."""
    pass


class ScanResultNotFoundError(ValidationError):
    """Raised when scan result is not found."""
    pass


class UndoWindowExpiredError(ValidationError):
    """Raised when undo window has expired."""
    pass


class ValidationService:
    """
    Validation service for handling user validation feedback.
    
    Implements:
    - Single validation submission (Requirement 1.2)
    - Batch validation (Requirement 2.3)
    - Undo validation within time window (Requirement 7.2)
    - Validation statistics (Requirement 4.2)
    - Retraining threshold checking (Requirement 5.1)
    """

    def __init__(self, db: AsyncSession):
        """Initialize the validation service with database session."""
        self.db = db
        self._retraining_threshold = getattr(
            settings, 'retraining_threshold', DEFAULT_RETRAINING_THRESHOLD
        )

    async def submit_validation(
        self,
        scan_result_id: UUID,
        user_id: UUID,
        is_correct: bool,
        corrected_label: bool | None = None,
    ) -> ValidationFeedback:
        """
        Submit a single validation for a scan result.
        
        Args:
            scan_result_id: ID of the scan result being validated
            user_id: ID of the user submitting the validation
            is_correct: True if user confirms prediction is correct
            corrected_label: Required if is_correct=False. True=gambling, False=clean
            
        Returns:
            The created or updated ValidationFeedback record
            
        Raises:
            ScanResultNotFoundError: If scan result doesn't exist
            ValidationError: If corrected_label missing when is_correct=False
            
        Requirements: 1.2
        """
        # Fetch the scan result
        result = await self.db.execute(
            select(ScanResult).where(ScanResult.id == scan_result_id)
        )
        scan_result = result.scalar_one_or_none()
        
        if scan_result is None:
            raise ScanResultNotFoundError(
                f"Scan result with id {scan_result_id} not found"
            )
        
        # Determine the corrected label
        if is_correct:
            # User confirms the prediction is correct
            final_label = scan_result.is_gambling
            is_correction = False
        else:
            # User is correcting the prediction
            if corrected_label is None:
                raise ValidationError(
                    "corrected_label is required when is_correct=False"
                )
            final_label = corrected_label
            is_correction = True
        
        # Check for existing validation (update if exists)
        existing_result = await self.db.execute(
            select(ValidationFeedback).where(
                and_(
                    ValidationFeedback.scan_result_id == scan_result_id,
                    ValidationFeedback.user_id == user_id,
                )
            )
        )
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            # Update existing validation
            existing.corrected_label = final_label
            existing.is_correction = is_correction
            existing.validated_at = datetime.now(timezone.utc)
            existing.used_in_training = False  # Reset training flag on update
            validation = existing
        else:
            # Create new validation
            validation = ValidationFeedback(
                scan_result_id=scan_result_id,
                user_id=user_id,
                comment_text=scan_result.comment_text or "",
                original_prediction=scan_result.is_gambling,
                original_confidence=scan_result.confidence,
                corrected_label=final_label,
                is_correction=is_correction,
                used_in_training=False,
            )
            self.db.add(validation)
        
        await self.db.commit()
        await self.db.refresh(validation)
        
        return validation

    async def batch_validate(
        self,
        result_ids: list[UUID],
        user_id: UUID,
        action: Literal['confirm_all', 'mark_gambling', 'mark_clean'],
    ) -> BatchValidationResult:
        """
        Submit batch validation for multiple scan results.
        
        Args:
            result_ids: List of scan result IDs to validate
            user_id: ID of the user submitting the validations
            action: Batch action to apply
                - 'confirm_all': Confirm all predictions as correct
                - 'mark_gambling': Mark all as gambling
                - 'mark_clean': Mark all as clean
                
        Returns:
            BatchValidationResult with success/failure counts
            
        Requirements: 2.3
        """
        successful = 0
        failed = 0
        validations: list[ValidationResponse] = []
        errors: list[str] = []
        
        for result_id in result_ids:
            try:
                if action == 'confirm_all':
                    validation = await self.submit_validation(
                        scan_result_id=result_id,
                        user_id=user_id,
                        is_correct=True,
                    )
                elif action == 'mark_gambling':
                    validation = await self.submit_validation(
                        scan_result_id=result_id,
                        user_id=user_id,
                        is_correct=False,
                        corrected_label=True,
                    )
                else:  # mark_clean
                    validation = await self.submit_validation(
                        scan_result_id=result_id,
                        user_id=user_id,
                        is_correct=False,
                        corrected_label=False,
                    )
                
                validations.append(ValidationResponse(
                    id=validation.id,
                    scan_result_id=validation.scan_result_id,
                    is_correction=validation.is_correction,
                    corrected_label=validation.corrected_label,
                    validated_at=validation.validated_at,
                    can_undo=self._can_undo(validation.validated_at),
                ))
                successful += 1
                
            except Exception as e:
                failed += 1
                errors.append(f"Failed to validate {result_id}: {str(e)}")
        
        return BatchValidationResult(
            total_submitted=len(result_ids),
            successful=successful,
            failed=failed,
            validations=validations,
            errors=errors,
        )

    async def undo_validation(
        self,
        validation_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Undo a validation within the time window.
        
        Args:
            validation_id: ID of the validation to undo
            user_id: ID of the user (must match validation owner)
            
        Returns:
            True if undo was successful
            
        Raises:
            ValidationNotFoundError: If validation doesn't exist or doesn't belong to user
            UndoWindowExpiredError: If undo window has expired
            
        Requirements: 7.2
        """
        # Fetch the validation
        result = await self.db.execute(
            select(ValidationFeedback).where(
                and_(
                    ValidationFeedback.id == validation_id,
                    ValidationFeedback.user_id == user_id,
                )
            )
        )
        validation = result.scalar_one_or_none()
        
        if validation is None:
            raise ValidationNotFoundError(
                f"Validation with id {validation_id} not found for user"
            )
        
        # Check if within undo window
        if not self._can_undo(validation.validated_at):
            raise UndoWindowExpiredError(
                "Undo window has expired (5 seconds)"
            )
        
        # Delete the validation
        await self.db.delete(validation)
        await self.db.commit()
        
        return True

    async def get_validation_stats(
        self,
        user_id: UUID | None = None,
    ) -> ValidationStats:
        """
        Get validation statistics.
        
        Args:
            user_id: Optional user ID to filter stats for specific user
            
        Returns:
            ValidationStats with counts and progress
            
        Requirements: 4.2
        """
        # Build base query
        base_query = select(ValidationFeedback)
        if user_id:
            base_query = base_query.where(ValidationFeedback.user_id == user_id)
        
        # Total validated count
        total_result = await self.db.execute(
            select(func.count(ValidationFeedback.id)).select_from(
                base_query.subquery()
            )
        )
        total_validated = total_result.scalar() or 0
        
        # Corrections count
        corrections_query = base_query.where(ValidationFeedback.is_correction == True)
        corrections_result = await self.db.execute(
            select(func.count(ValidationFeedback.id)).select_from(
                corrections_query.subquery()
            )
        )
        corrections_made = corrections_result.scalar() or 0
        
        # Pending for training (not yet used in training)
        pending_query = select(ValidationFeedback).where(
            ValidationFeedback.used_in_training == False
        )
        pending_result = await self.db.execute(
            select(func.count(ValidationFeedback.id)).select_from(
                pending_query.subquery()
            )
        )
        pending_for_training = pending_result.scalar() or 0
        
        # Calculate progress
        threshold = self._retraining_threshold
        progress_percent = min(
            (pending_for_training / threshold) * 100 if threshold > 0 else 0,
            100.0
        )
        
        return ValidationStats(
            total_validated=total_validated,
            corrections_made=corrections_made,
            pending_for_training=pending_for_training,
            threshold=threshold,
            progress_percent=round(progress_percent, 2),
        )

    async def check_retraining_threshold(self) -> bool:
        """
        Check if the retraining threshold has been reached.
        
        Returns:
            True if pending validations >= threshold
            
        Requirements: 5.1
        """
        # Count validations not yet used in training
        result = await self.db.execute(
            select(func.count(ValidationFeedback.id)).where(
                ValidationFeedback.used_in_training == False
            )
        )
        pending_count = result.scalar() or 0
        
        return pending_count >= self._retraining_threshold

    def _can_undo(self, validated_at: datetime) -> bool:
        """
        Check if a validation can still be undone.
        
        Args:
            validated_at: Timestamp when validation was created
            
        Returns:
            True if within undo window
        """
        now = datetime.now(timezone.utc)
        # Ensure validated_at is timezone-aware
        if validated_at.tzinfo is None:
            validated_at = validated_at.replace(tzinfo=timezone.utc)
        
        elapsed = (now - validated_at).total_seconds()
        return elapsed <= UNDO_WINDOW_SECONDS

    async def get_validations_for_scan(
        self,
        scan_id: UUID,
        user_id: UUID,
    ) -> list[ValidationFeedback]:
        """
        Get all validations for a specific scan by the current user.
        
        Args:
            scan_id: ID of the scan
            user_id: ID of the user
            
        Returns:
            List of ValidationFeedback records
        """
        # Get all scan results for this scan
        from app.models.scan import Scan
        
        result = await self.db.execute(
            select(ValidationFeedback)
            .join(ScanResult, ValidationFeedback.scan_result_id == ScanResult.id)
            .join(Scan, ScanResult.scan_id == Scan.id)
            .where(
                and_(
                    Scan.id == scan_id,
                    ValidationFeedback.user_id == user_id,
                )
            )
        )
        
        return list(result.scalars().all())
