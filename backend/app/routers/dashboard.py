"""
Dashboard Router for statistics and export operations.

Endpoints:
- GET /api/dashboard/stats - Get overview statistics
- GET /api/dashboard/chart-data - Get chart data for past 30 days
- GET /api/dashboard/export/{scan_id} - Export scan results (CSV/JSON)

Requirements: 7.1, 7.2, 8.1, 8.2, 8.3
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import func, select, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.scan import Scan, ScanResult
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.export_service import ExportService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get overview statistics for the current user.
    
    Returns total scans, total comments analyzed, and gambling detection rate.
    
    Requirements: 7.1
    """
    # Get total scans count
    total_scans_query = select(func.count(Scan.id)).where(
        Scan.user_id == current_user.id
    )
    total_scans_result = await db.execute(total_scans_query)
    total_scans = total_scans_result.scalar() or 0
    
    # Get aggregated comment statistics from completed scans
    stats_query = select(
        func.coalesce(func.sum(Scan.total_comments), 0).label("total_comments"),
        func.coalesce(func.sum(Scan.gambling_count), 0).label("total_gambling"),
        func.coalesce(func.sum(Scan.clean_count), 0).label("total_clean"),
    ).where(
        Scan.user_id == current_user.id,
        Scan.status == "completed",
    )
    stats_result = await db.execute(stats_query)
    stats = stats_result.one()
    
    total_comments = int(stats.total_comments)
    total_gambling = int(stats.total_gambling)
    
    # Calculate gambling detection rate
    gambling_detection_rate = 0.0
    if total_comments > 0:
        gambling_detection_rate = total_gambling / total_comments
    
    return {
        "total_scans": total_scans,
        "total_comments": total_comments,
        "total_gambling": total_gambling,
        "gambling_detection_rate": gambling_detection_rate,
    }



@router.get("/chart-data")
async def get_chart_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get chart data for scans over the past 30 days.
    
    Returns time-series data with scan counts aggregated by date.
    
    Requirements: 7.2
    """
    # Calculate date range (past 30 days)
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=29)  # 30 days including today
    
    # Query scan counts grouped by date
    query = (
        select(
            cast(Scan.created_at, Date).label("date"),
            func.count(Scan.id).label("scan_count"),
            func.coalesce(func.sum(Scan.total_comments), 0).label("total_comments"),
            func.coalesce(func.sum(Scan.gambling_count), 0).label("gambling_count"),
        )
        .where(
            Scan.user_id == current_user.id,
            cast(Scan.created_at, Date) >= start_date,
            cast(Scan.created_at, Date) <= end_date,
        )
        .group_by(cast(Scan.created_at, Date))
        .order_by(cast(Scan.created_at, Date))
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    # Create a dict for quick lookup
    data_by_date = {
        row.date: {
            "scan_count": row.scan_count,
            "total_comments": int(row.total_comments),
            "gambling_count": int(row.gambling_count),
        }
        for row in rows
    }
    
    # Generate data points for all 30 days (fill missing days with zeros)
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
                "scan_count": 0,
                "total_comments": 0,
                "gambling_count": 0,
            })
        current_date += timedelta(days=1)
    
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "data_points": data_points,
    }


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
