"""
ModelVersion SQLAlchemy model for tracking ML model versions.
Requirements: 5.3
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ModelVersion(Base):
    """
    ModelVersion model for tracking ML model versions and their performance metrics.
    
    Supports model versioning, rollback capability, and performance tracking.
    Requirements: 5.3
    """

    __tablename__ = "model_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    version: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Training statistics
    training_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    validation_samples: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Performance metrics
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    precision_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    recall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    f1_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deactivated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    validations: Mapped[list["ValidationFeedback"]] = relationship(
        "ValidationFeedback", back_populates="model_version"
    )

    # Indexes for performance
    __table_args__ = (
        Index("ix_model_versions_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<ModelVersion(id={self.id}, version={self.version}, is_active={self.is_active})>"
