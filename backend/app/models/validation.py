"""
ValidationFeedback SQLAlchemy model for storing user validation data.
Requirements: 9.1, 9.2
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ValidationFeedback(Base):
    """
    ValidationFeedback model for storing user corrections to model predictions.
    
    Stores the comment text, original prediction, user's correction, and metadata
    for use in model retraining.
    Requirements: 9.1, 9.2
    """

    __tablename__ = "validation_feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scan_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scan_results.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Comment data for training
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Original model prediction
    original_prediction: Mapped[bool] = mapped_column(Boolean, nullable=False)
    original_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    
    # User's correction
    corrected_label: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_correction: Mapped[bool] = mapped_column(Boolean, nullable=False)
    
    # Timestamps
    validated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    # Training tracking
    used_in_training: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    model_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("model_versions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    scan_result: Mapped["ScanResult"] = relationship("ScanResult")
    user: Mapped["User"] = relationship("User")
    model_version: Mapped["ModelVersion"] = relationship("ModelVersion", back_populates="validations")

    # Indexes for performance
    __table_args__ = (
        Index("ix_validation_feedback_user_id", "user_id"),
        Index("ix_validation_feedback_used_in_training", "used_in_training"),
        Index("ix_validation_feedback_is_correction", "is_correction"),
        # Unique constraint: one validation per user per scan result
        Index("ix_validation_feedback_unique", "scan_result_id", "user_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<ValidationFeedback(id={self.id}, is_correction={self.is_correction})>"
