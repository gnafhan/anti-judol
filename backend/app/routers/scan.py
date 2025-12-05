"""
Scan Router for video comment scanning operations.

Endpoints:
- POST /api/scan - Create a new scan (queued)
- GET /api/scan/history - Get paginated scan history
- GET /api/scan/{scan_id} - Get scan details with results
- GET /api/scan/{scan_id}/status - Get scan status for polling
- DELETE /api/scan/{scan_id} - Delete scan and cascade to results

Requirements: 3.1, 3.7, 7.3, 7.4, 9.1, 10.3
"""

import uuid
from math import ceil
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.scan import Scan, ScanResult
from app.models.user import User
from app.schemas.scan import (
    ScanCreate,
    ScanResponse,
    ScanDetailResponse,
    ScanListResponse,
    ScanResultResponse,
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/scan", tags=["scan"])

# In-memory task store (temporary until Celery is implemented in Phase 4)
_task_store: dict[str, dict[str, Any]] = {}


@router.post("/", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    request: ScanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScanResponse:
    """
    Create a new video scan.
    
    Creates a scan record with status "pending" and queues a Celery task
    for processing. Returns scan_id and task_id immediately.
    
    Requirements: 3.1, 9.1
    """
    # Generate task_id for the Celery task
    # Note: Full Celery integration will be implemented in Phase 4
    task_id = str(uuid.uuid4())
    
    # Create scan record with pending status (Requirement 3.1)
    scan = Scan(
        user_id=current_user.id,
        video_id=request.video_id,
        status="pending",
        task_id=task_id,
    )
    
    db.add(scan)
    await db.commit()
    await db.refresh(scan)
    
    # Store task info (temporary until Celery is implemented)
    _task_store[task_id] = {
        "scan_id": str(scan.id),
        "status": "pending",
    }
    
    # TODO: Queue Celery task in Phase 4
    # scan_video_comments.delay(str(scan.id), request.video_id, str(current_user.id))
    
    return ScanResponse(
        id=scan.id,
        video_id=scan.video_id,
        video_title=scan.video_title,
        status=scan.status,
        task_id=scan.task_id,
        created_at=scan.created_at,
    )


@router.get("/history", response_model=ScanListResponse)
async def get_scan_history(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScanListResponse:
    """
    Get paginated scan history for the current user.
    
    Returns a list of scans with summary statistics.
    
    Requirements: 7.3
    """
    # Count total scans for the user
    count_query = select(func.count(Scan.id)).where(Scan.user_id == current_user.id)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Calculate pagination
    pages = ceil(total / limit) if total > 0 else 1
    offset = (page - 1) * limit
    
    # Fetch scans with pagination
    query = (
        select(Scan)
        .where(Scan.user_id == current_user.id)
        .order_by(Scan.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    scans = result.scalars().all()
    
    # Convert to response models
    items = [
        ScanResponse(
            id=scan.id,
            video_id=scan.video_id,
            video_title=scan.video_title,
            status=scan.status,
            task_id=scan.task_id,
            created_at=scan.created_at,
        )
        for scan in scans
    ]
    
    return ScanListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


@router.get("/{scan_id}", response_model=ScanDetailResponse)
async def get_scan(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScanDetailResponse:
    """
    Get scan details with all results.
    
    Returns complete scan information including all scan results.
    
    Requirements: 7.4
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
    
    # Convert results to response models
    results = [
        ScanResultResponse(
            id=r.id,
            comment_id=r.comment_id,
            comment_text=r.comment_text or "",
            author_name=r.author_name,
            is_gambling=r.is_gambling,
            confidence=r.confidence,
        )
        for r in scan.results
    ]
    
    return ScanDetailResponse(
        id=scan.id,
        video_id=scan.video_id,
        video_title=scan.video_title,
        status=scan.status,
        task_id=scan.task_id,
        created_at=scan.created_at,
        video_thumbnail=scan.video_thumbnail,
        channel_name=scan.channel_name,
        total_comments=scan.total_comments,
        gambling_count=scan.gambling_count,
        clean_count=scan.clean_count,
        scanned_at=scan.scanned_at,
        results=results,
    )


@router.get("/{scan_id}/status")
async def get_scan_status(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get current scan status for polling.
    
    Returns the current status of a scan for frontend polling.
    
    Requirements: 3.7
    """
    # Fetch scan (without results for efficiency)
    query = select(Scan).where(Scan.id == scan_id, Scan.user_id == current_user.id)
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
    
    response = {
        "scan_id": str(scan.id),
        "status": scan.status,
        "task_id": scan.task_id,
    }
    
    # Include counts if scan is completed
    if scan.status == "completed":
        response.update({
            "total_comments": scan.total_comments,
            "gambling_count": scan.gambling_count,
            "clean_count": scan.clean_count,
        })
    
    # Include error message if scan failed
    if scan.status == "failed" and scan.error_message:
        response["error_message"] = scan.error_message
    
    return response


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a scan and cascade to results.
    
    Deletes the scan record and all associated scan results.
    
    Requirements: 10.3
    """
    # Fetch scan
    query = select(Scan).where(Scan.id == scan_id, Scan.user_id == current_user.id)
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
    
    # Delete scan (cascade will delete results)
    await db.delete(scan)
    await db.commit()
    
    # Clean up task store if exists
    if scan.task_id and scan.task_id in _task_store:
        del _task_store[scan.task_id]
