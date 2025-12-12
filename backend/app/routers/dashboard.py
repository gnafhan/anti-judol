"""
Dashboard Router for statistics and export operations.

Endpoints:
- GET /api/dashboard/stats - Get overview statistics (with filters)
- GET /api/dashboard/chart-data - Get chart data for past 30 days (with filters)
- GET /api/dashboard/scanned-videos - Get list of scanned videos for filter
- GET /api/dashboard/top-videos - Get top videos by gambling count
- GET /api/dashboard/export/{scan_id} - Export scan results (CSV/JSON)
- GET /api/dashboard/model-metrics - Get model metrics for dashboard display
- GET /api/dashboard/model-improvement - Get latest model improvement notification
- GET /api/dashboard/validation-contributions - Get user's validation contributions

Requirements: 7.1, 7.2, 8.1, 8.2, 8.3, 10.1, 10.2, 10.3
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import func, select, cast, Date, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.scan import Scan, ScanResult
from app.models.user import User
from app.models.model_version import ModelVersion
from app.models.validation import ValidationFeedback
from app.services.auth_service import get_current_user
from app.services.export_service import ExportService


# Response schemas for model metrics
class ModelMetricsResponse(BaseModel):
    """Model metrics for dashboard display."""
    current_version: str | None
    accuracy: float | None
    precision: float | None
    recall: float | None
    f1_score: float | None
    training_samples: int | None
    validation_samples: int | None
    last_trained: str | None


class ModelImprovementResponse(BaseModel):
    """Model improvement notification data."""
    has_improvement: bool
    previous_version: str | None
    new_version: str | None
    accuracy_change: float | None
    improvement_percent: float | None
    deployed_at: str | None


class ValidationContributionResponse(BaseModel):
    """User's validation contribution data."""
    total_validations: int
    contributed_to_training: int
    corrections_made: int
    model_versions_contributed: int

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def build_scan_filter(
    base_query,
    user_id: uuid.UUID,
    video_ids: list[str] | None = None,
    source: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
):
    """Build common filter conditions for dashboard queries."""
    conditions = [Scan.user_id == user_id]
    
    if video_ids:
        conditions.append(Scan.video_id.in_(video_ids))
    
    # Source filter: 'my_videos' or 'public' based on is_own_video flag
    if source == "my_videos":
        conditions.append(Scan.is_own_video == True)
    elif source == "public":
        conditions.append(Scan.is_own_video == False)
    # 'all' or None means no source filter
    
    if start_date:
        conditions.append(Scan.created_at >= start_date)
    
    if end_date:
        conditions.append(Scan.created_at <= end_date)
    
    return base_query.where(and_(*conditions))


@router.get("/stats")
async def get_stats(
    video_ids: str | None = Query(None, description="Comma-separated video IDs to filter"),
    source: str | None = Query(None, description="Source filter: all, my_videos, public"),
    start_date: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get overview statistics for the current user with optional filters.
    
    Returns total scans, total comments analyzed, and gambling detection rate.
    
    Requirements: 7.1
    """
    # Parse filters
    video_id_list = video_ids.split(",") if video_ids else None
    parsed_start = datetime.fromisoformat(start_date) if start_date else None
    parsed_end = datetime.fromisoformat(end_date) if end_date else None
    
    # Build base query for total scans
    total_scans_query = select(func.count(Scan.id))
    total_scans_query = build_scan_filter(
        total_scans_query, current_user.id, video_id_list, source, parsed_start, parsed_end
    )
    total_scans_result = await db.execute(total_scans_query)
    total_scans = total_scans_result.scalar() or 0
    
    # Build query for aggregated statistics
    stats_query = select(
        func.coalesce(func.sum(Scan.total_comments), 0).label("total_comments"),
        func.coalesce(func.sum(Scan.gambling_count), 0).label("total_gambling"),
        func.coalesce(func.sum(Scan.clean_count), 0).label("total_clean"),
    )
    stats_query = build_scan_filter(
        stats_query, current_user.id, video_id_list, source, parsed_start, parsed_end
    )
    stats_query = stats_query.where(Scan.status == "completed")
    
    stats_result = await db.execute(stats_query)
    stats = stats_result.one()
    
    total_comments = int(stats.total_comments)
    total_gambling = int(stats.total_gambling)
    total_clean = int(stats.total_clean)
    
    # Calculate gambling detection rate
    gambling_detection_rate = 0.0
    if total_comments > 0:
        gambling_detection_rate = total_gambling / total_comments
    
    return {
        "total_scans": total_scans,
        "total_comments": total_comments,
        "gambling_comments": total_gambling,
        "clean_comments": total_clean,
        "detection_rate": gambling_detection_rate,
    }



@router.get("/chart-data")
async def get_chart_data(
    video_ids: str | None = Query(None, description="Comma-separated video IDs to filter"),
    source: str | None = Query(None, description="Source filter: all, my_videos, public"),
    days: int = Query(30, ge=7, le=90, description="Number of days to show"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get chart data for scans over the specified period.
    
    Returns time-series data with scan counts aggregated by date.
    
    Requirements: 7.2
    """
    # Parse filters
    video_id_list = video_ids.split(",") if video_ids else None
    
    # Calculate date range
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=days - 1)
    
    # Build base query
    base_conditions = [
        Scan.user_id == current_user.id,
        cast(Scan.created_at, Date) >= start_date,
        cast(Scan.created_at, Date) <= end_date,
    ]
    
    if video_id_list:
        base_conditions.append(Scan.video_id.in_(video_id_list))
    
    # Source filter
    if source == "my_videos":
        base_conditions.append(Scan.is_own_video == True)
    elif source == "public":
        base_conditions.append(Scan.is_own_video == False)
    
    query = (
        select(
            cast(Scan.created_at, Date).label("date"),
            func.count(Scan.id).label("scan_count"),
            func.coalesce(func.sum(Scan.total_comments), 0).label("total_comments"),
            func.coalesce(func.sum(Scan.gambling_count), 0).label("gambling_count"),
            func.coalesce(func.sum(Scan.clean_count), 0).label("clean_count"),
        )
        .where(and_(*base_conditions))
        .group_by(cast(Scan.created_at, Date))
        .order_by(cast(Scan.created_at, Date))
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    # Create a dict for quick lookup
    data_by_date = {
        row.date: {
            "scans": row.scan_count,
            "gambling_count": int(row.gambling_count),
            "clean_count": int(row.clean_count),
        }
        for row in rows
    }
    
    # Generate data points for all days (fill missing days with zeros)
    data_points = []
    current_date = start_date
    while current_date <= end_date:
        if current_date in data_by_date:
            data_points.append({
                "date": current_date.isoformat(),
                **data_by_date[current_date],
            })
        else:
            data_points.append({
                "date": current_date.isoformat(),
                "scans": 0,
                "gambling_count": 0,
                "clean_count": 0,
            })
        current_date += timedelta(days=1)
    
    return {
        "data": data_points,
    }


@router.get("/scanned-videos")
async def get_scanned_videos(
    source: str | None = Query(None, description="Source filter: all, my_videos, public"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get list of all scanned videos for filter dropdown.
    
    Returns unique videos that have been scanned by the user.
    Includes is_own_video flag based on whether video was scanned from my-videos page.
    """
    base_conditions = [Scan.user_id == current_user.id, Scan.status == "completed"]
    
    # Source filter
    if source == "my_videos":
        base_conditions.append(Scan.is_own_video == True)
    elif source == "public":
        base_conditions.append(Scan.is_own_video == False)
    
    query = (
        select(
            Scan.video_id,
            Scan.video_title,
            Scan.video_thumbnail,
            Scan.channel_name,
            Scan.is_own_video,
            func.count(Scan.id).label("scan_count"),
            func.max(Scan.created_at).label("last_scanned"),
        )
        .where(and_(*base_conditions))
        .group_by(Scan.video_id, Scan.video_title, Scan.video_thumbnail, Scan.channel_name, Scan.is_own_video)
        .order_by(func.max(Scan.created_at).desc())
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    videos = [
        {
            "video_id": row.video_id,
            "video_title": row.video_title,
            "video_thumbnail": row.video_thumbnail,
            "channel_name": row.channel_name,
            "scan_count": row.scan_count,
            "last_scanned": row.last_scanned.isoformat() if row.last_scanned else None,
            "is_own_video": row.is_own_video if row.is_own_video is not None else False,
        }
        for row in rows
    ]
    
    return {"videos": videos}


@router.get("/top-videos")
async def get_top_videos(
    video_ids: str | None = Query(None, description="Comma-separated video IDs to filter"),
    source: str | None = Query(None, description="Source filter: all, my_videos, public"),
    limit: int = Query(10, ge=1, le=50, description="Number of videos to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get top videos by gambling comment count.
    
    Returns videos sorted by gambling comments detected.
    """
    video_id_list = video_ids.split(",") if video_ids else None
    
    base_conditions = [
        Scan.user_id == current_user.id,
        Scan.status == "completed",
    ]
    
    if video_id_list:
        base_conditions.append(Scan.video_id.in_(video_id_list))
    
    # Source filter
    if source == "my_videos":
        base_conditions.append(Scan.is_own_video == True)
    elif source == "public":
        base_conditions.append(Scan.is_own_video == False)
    
    query = (
        select(
            Scan.video_id,
            Scan.video_title,
            Scan.video_thumbnail,
            Scan.channel_name,
            func.sum(Scan.gambling_count).label("total_gambling"),
            func.sum(Scan.clean_count).label("total_clean"),
            func.sum(Scan.total_comments).label("total_comments"),
        )
        .where(and_(*base_conditions))
        .group_by(Scan.video_id, Scan.video_title, Scan.video_thumbnail, Scan.channel_name)
        .order_by(func.sum(Scan.gambling_count).desc())
        .limit(limit)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    videos = [
        {
            "video_id": row.video_id,
            "video_title": row.video_title,
            "video_thumbnail": row.video_thumbnail,
            "channel_name": row.channel_name,
            "gambling_count": int(row.total_gambling or 0),
            "clean_count": int(row.total_clean or 0),
            "total_comments": int(row.total_comments or 0),
            "detection_rate": (
                int(row.total_gambling or 0) / int(row.total_comments)
                if row.total_comments and int(row.total_comments) > 0
                else 0
            ),
        }
        for row in rows
    ]
    
    return {"videos": videos}


@router.get("/export/{scan_id}")
async def export_scan(
    scan_id: uuid.UUID,
    format: str = Query("csv", regex="^(csv|json)$", description="Export format"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Export scan results in CSV or JSON format.
    
    Generates a downloadable file with scan results and metadata.
    
    Requirements: 8.1, 8.2, 8.3
    """
    # Fetch scan with results
    query = (
        select(Scan)
        .options(selectinload(Scan.results))
        .where(Scan.id == scan_id, Scan.user_id == current_user.id)
    )
    result = await db.execute(query)
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Scan Not Found",
                "error_code": "scan_not_found",
                "message": f"Scan with ID '{scan_id}' not found",
            },
        )
    
    export_service = ExportService()
    
    if format == "csv":
        content = export_service.export_csv(scan, scan.results)
        media_type = "text/csv"
        filename = f"scan_{scan_id}.csv"
    else:
        content = export_service.export_json(scan, scan.results)
        media_type = "application/json"
        filename = f"scan_{scan_id}.json"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/model-metrics", response_model=ModelMetricsResponse)
async def get_model_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelMetricsResponse:
    """
    Get model metrics for dashboard display.
    
    Returns current model version, accuracy, and other performance metrics.
    Available to all authenticated users.
    
    Requirements: 10.1
    """
    # Get active model
    result = await db.execute(
        select(ModelVersion).where(ModelVersion.is_active == True)
    )
    active_model = result.scalar_one_or_none()
    
    if active_model:
        return ModelMetricsResponse(
            current_version=active_model.version,
            accuracy=active_model.accuracy,
            precision=active_model.precision_score,
            recall=active_model.recall_score,
            f1_score=active_model.f1_score,
            training_samples=active_model.training_samples,
            validation_samples=active_model.validation_samples,
            last_trained=active_model.activated_at.isoformat() if active_model.activated_at else None,
        )
    
    return ModelMetricsResponse(
        current_version=None,
        accuracy=None,
        precision=None,
        recall=None,
        f1_score=None,
        training_samples=None,
        validation_samples=None,
        last_trained=None,
    )


@router.get("/model-improvement", response_model=ModelImprovementResponse)
async def get_model_improvement(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelImprovementResponse:
    """
    Get latest model improvement notification data.
    
    Compares the current active model with the previous version to show
    improvement percentage.
    
    Requirements: 10.2
    """
    # Get the two most recent model versions
    result = await db.execute(
        select(ModelVersion)
        .order_by(ModelVersion.created_at.desc())
        .limit(2)
    )
    versions = result.scalars().all()
    
    if len(versions) < 2:
        return ModelImprovementResponse(
            has_improvement=False,
            previous_version=None,
            new_version=versions[0].version if versions else None,
            accuracy_change=None,
            improvement_percent=None,
            deployed_at=versions[0].activated_at.isoformat() if versions and versions[0].activated_at else None,
        )
    
    new_model = versions[0]
    previous_model = versions[1]
    
    # Calculate improvement
    accuracy_change = None
    improvement_percent = None
    has_improvement = False
    
    if new_model.accuracy is not None and previous_model.accuracy is not None:
        accuracy_change = new_model.accuracy - previous_model.accuracy
        if previous_model.accuracy > 0:
            improvement_percent = (accuracy_change / previous_model.accuracy) * 100
        has_improvement = accuracy_change > 0
    
    return ModelImprovementResponse(
        has_improvement=has_improvement,
        previous_version=previous_model.version,
        new_version=new_model.version,
        accuracy_change=round(accuracy_change, 4) if accuracy_change is not None else None,
        improvement_percent=round(improvement_percent, 2) if improvement_percent is not None else None,
        deployed_at=new_model.activated_at.isoformat() if new_model.activated_at else None,
    )


@router.get("/validation-contributions", response_model=ValidationContributionResponse)
async def get_validation_contributions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ValidationContributionResponse:
    """
    Get user's validation contribution statistics.
    
    Shows how many validations the user has submitted and how many
    contributed to model improvements.
    
    Requirements: 10.3
    """
    user_id = current_user.id
    
    # Total validations by user
    total_result = await db.execute(
        select(func.count(ValidationFeedback.id)).where(
            ValidationFeedback.user_id == user_id
        )
    )
    total_validations = total_result.scalar() or 0
    
    # Validations that contributed to training
    contributed_result = await db.execute(
        select(func.count(ValidationFeedback.id)).where(
            and_(
                ValidationFeedback.user_id == user_id,
                ValidationFeedback.used_in_training == True,
            )
        )
    )
    contributed_to_training = contributed_result.scalar() or 0
    
    # Corrections made (where user disagreed with model)
    corrections_result = await db.execute(
        select(func.count(ValidationFeedback.id)).where(
            and_(
                ValidationFeedback.user_id == user_id,
                ValidationFeedback.is_correction == True,
            )
        )
    )
    corrections_made = corrections_result.scalar() or 0
    
    # Count distinct model versions the user contributed to
    versions_result = await db.execute(
        select(func.count(func.distinct(ValidationFeedback.model_version_id))).where(
            and_(
                ValidationFeedback.user_id == user_id,
                ValidationFeedback.used_in_training == True,
                ValidationFeedback.model_version_id.isnot(None),
            )
        )
    )
    model_versions_contributed = versions_result.scalar() or 0
    
    return ValidationContributionResponse(
        total_validations=total_validations,
        contributed_to_training=contributed_to_training,
        corrections_made=corrections_made,
        model_versions_contributed=model_versions_contributed,
    )
