"""YouTube Pydantic schemas matching YouTube API response structure.

Requirements: 4.2, 5.2
"""
from datetime import datetime

from pydantic import BaseModel


class VideoInfo(BaseModel):
    """Schema for YouTube video information."""
    id: str
    title: str
    description: str | None = None
    thumbnail_url: str
    channel_name: str
    channel_id: str
    view_count: int
    comment_count: int
    published_at: datetime


class CommentInfo(BaseModel):
    """Schema for YouTube comment information."""
    id: str
    text: str
    author_name: str
    author_avatar: str | None = None
    author_channel_id: str | None = None
    like_count: int
    published_at: datetime


class VideoListResponse(BaseModel):
    """Schema for paginated video list response."""
    items: list[VideoInfo]
    next_page_token: str | None = None
    total_results: int


class CommentListResponse(BaseModel):
    """Schema for paginated comment list response."""
    items: list[CommentInfo]
    next_page_token: str | None = None
    total_results: int
