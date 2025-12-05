"""Scan Pydantic schemas for scan CRUD operations.

Requirements: 3.1, 7.3
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ScanCreate(BaseModel):
    """Schema for creating a new scan."""
    video_id: str
    video_url: str | None = None


class ScanResponse(BaseModel):
    """Basic scan response schema."""
    id: UUID
    video_id: str
    video_title: str | None = None
    status: str
    task_id: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScanResultResponse(BaseModel):
    """Schema for individual scan result."""
    id: UUID
    comment_id: str
    comment_text: str
    author_name: str | None = None
    is_gambling: bool
    confidence: float

    model_config = ConfigDict(from_attributes=True)


class ScanDetailResponse(ScanResponse):
    """Detailed scan response with results."""
    video_thumbnail: str | None = None
    channel_name: str | None = None
    total_comments: int = 0
    gambling_count: int = 0
    clean_count: int = 0
    scanned_at: datetime | None = None
    results: list[ScanResultResponse] = []


class ScanListResponse(BaseModel):
    """Paginated list of scans."""
    items: list[ScanResponse]
    total: int
    page: int
    limit: int
    pages: int
