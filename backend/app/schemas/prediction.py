"""Prediction Pydantic schemas with validation constraints.

Requirements: 2.2, 2.3, 2.4
"""
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Schema for batch prediction request."""
    texts: list[str] = Field(..., min_length=1, max_length=1000)
    async_mode: bool = False


class PredictionResponse(BaseModel):
    """Schema for single prediction response."""
    text: str
    is_gambling: bool
    confidence: float = Field(..., ge=0.0, le=1.0)


class BatchPredictionResponse(BaseModel):
    """Schema for batch prediction response."""
    predictions: list[PredictionResponse]
    task_id: str | None = None
