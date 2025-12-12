"""
Scan and ScanResult SQLAlchemy models for storing video scan data.
Requirements: 3.1, 3.4, 3.5, 10.2, 10.3
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Scan(Base):
    """
    Scan model for storing video scan records.
    
    Tracks the status and results of scanning a YouTube video for gambling comments.
    Requirements: 3.1, 3.5, 10.2
    """

    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Video information
    video_id: Mapped[str] = mapped_column(String(50), nullable=False)
    video_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    video_thumbnail: Mapped[str | None] = mapped_column(String(500), nullable=True)
    channel_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_own_video: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Scan statistics (Requirement 3.5)
    total_comments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    gambling_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clean_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Status tracking (Requirement 3.1)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending/processing/completed/failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Timestamps (UTC - Requirement 10.5)
    scanned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="scans")
    results: Mapped[list["ScanResult"]] = relationship(
        "ScanResult", back_populates="scan", cascade="all, delete-orphan"
    )

    # Indexes for performance
    __table_args__ = (
        Index("ix_scans_video_id", "video_id"),
        Index("ix_scans_status", "status"),
        Index("ix_scans_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<Scan(id={self.id}, video_id={self.video_id}, status={self.status})>"


class ScanResult(Base):
    """
    ScanResult model for storing individual comment predictions.
    
    Each result is linked to a scan via foreign key (Requirement 3.4, 10.2).
    Cascade delete ensures results are removed when scan is deleted (Requirement 10.3).
    """

    __tablename__ = "scan_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Comment information
    comment_id: Mapped[str] = mapped_column(String(255), nullable=False)
    comment_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Prediction results
    is_gambling: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Timestamps (UTC - Requirement 10.5)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    scan: Mapped["Scan"] = relationship("Scan", back_populates="results")

    # Indexes for performance
    __table_args__ = (
        Index("ix_scan_results_scan_id", "scan_id"),
        Index("ix_scan_results_is_gambling", "is_gambling"),
    )

    def __repr__(self) -> str:
        return f"<ScanResult(id={self.id}, is_gambling={self.is_gambling})>"
