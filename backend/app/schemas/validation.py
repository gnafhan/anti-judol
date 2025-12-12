"""
Validation Pydantic schemas for validation feedback operations.

Requirements: 1.2, 2.2
"""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ValidationSubmit(BaseModel):
    """Schema for submitting a single validation."""
    scan_result_id: UUID
    is_correct: bool
    corrected_label: bool | None = Field(
        default=None,
        description="Required if is_correct=False. True=gambling, False=clean"
    )


class BatchValidationSubmit(BaseModel):
    """Schema for submitting batch validation."""
    result_ids: list[UUID]
    action: Literal['confirm_all', 'mark_gambling', 'mark_clean']


class ValidationResponse(BaseModel):
    """Schema for validation response."""
    id: UUID
    scan_result_id: UUID
    is_correction: bool
    corrected_label: bool
    validated_at: datetime
    can_undo: bool = Field(
        default=True,
        description="True if within undo window (5 seconds)"
    )

    model_config = ConfigDict(from_attributes=True)


class ValidationStats(BaseModel):
    """Schema for validation statistics."""
    total_validated: int
    corrections_made: int
    pending_for_training: int
    threshold: int
    progress_percent: float = Field(
        ge=0.0,
        le=100.0,
        description="Progress toward retraining threshold (0-100)"
    )


class BatchValidationResult(BaseModel):
    """Schema for batch validation result."""
    total_submitted: int
    successful: int
    failed: int
    validations: list[ValidationResponse] = []
    errors: list[str] = []
