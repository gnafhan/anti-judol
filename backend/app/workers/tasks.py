"""
Celery tasks for background processing.

This module contains:
- scan_video_comments: Async task to scan video comments for gambling content
- batch_predict: Async batch prediction task
- cleanup_old_results: Periodic task to clean up old scan results

Requirements: 2.3, 3.2, 3.3, 3.4, 3.5, 9.2, 9.4, 9.5
"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from celery import shared_task
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import sessionmaker, Session

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Lazy initialization for database engine (created on first use)
_sync_engine = None
_SyncSessionLocal = None


def _get_sync_engine():
    """Get or create the sync database engine (lazy initialization)."""
    global _sync_engine, _SyncSessionLocal
    
    if _sync_engine is None:
        # Import models here to avoid circular imports
        from app.models.scan import Scan, ScanResult
        from app.models.user import User
        
        # Convert async URL to sync URL
        sync_database_url = settings.database_url.replace(
            "postgresql+asyncpg://", "postgresql://"
        )
        _sync_engine = create_engine(sync_database_url, pool_pre_ping=True)
        _SyncSessionLocal = sessionmaker(
            bind=_sync_engine, autocommit=False, autoflush=False
        )
    
    return _sync_engine, _SyncSessionLocal


def get_sync_db() -> Session:
    """Get a synchronous database session for Celery tasks."""
    _, SyncSessionLocal = _get_sync_engine()
    return SyncSessionLocal()


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def scan_video_comments(
    self,
    scan_id: str,
    video_id: str,
    user_id: str,
) -> dict:
    """
    Async task to scan video comments for gambling content.
    
    This task:
    1. Fetches all comments from YouTube API
    2. Runs ML prediction on each comment
    3. Stores results in database
    4. Updates scan status progressively
    5. Handles errors with retry logic
    
    Args:
        scan_id: UUID of the scan record
        video_id: YouTube video ID to scan
        user_id: UUID of the user who initiated the scan
        
    Returns:
        Dictionary with scan results summary
        
    Requirements: 3.2, 3.3, 3.4, 3.5, 9.2, 9.4
    """
    # Import models and services inside task to avoid import issues
    from app.models.scan import Scan, ScanResult
    from app.models.user import User
    from app.services.auth_service import AuthService
    from app.services.prediction_service import PredictionService
    from app.services.youtube_service import YouTubeService, YouTubeAPIError
    
    db = get_sync_db()
    
    try:
        # Get scan record
        scan = db.execute(
            select(Scan).where(Scan.id == UUID(scan_id))
        ).scalar_one_or_none()
        
        if not scan:
            logger.error(f"Scan {scan_id} not found")
            return {"error": "Scan not found"}
        
        # Update status to processing (Requirement 9.2)
        scan.status = "processing"
        db.commit()
        
        # Get user for OAuth tokens
        user = db.execute(
            select(User).where(User.id == UUID(user_id))
        ).scalar_one_or_none()
        
        if not user:
            scan.status = "failed"
            scan.error_message = "User not found"
            db.commit()
            return {"error": "User not found"}
        
        # Decrypt OAuth tokens
        auth_service = AuthService()
        
        try:
            access_token = auth_service.decrypt_token(user.access_token)
            refresh_token = None
            if user.refresh_token:
                refresh_token = auth_service.decrypt_token(user.refresh_token)
        except Exception as e:
            scan.status = "failed"
            scan.error_message = f"Failed to decrypt tokens: {str(e)}"
            db.commit()
            return {"error": "Token decryption failed"}
        
        # Create YouTube service with user's credentials
        youtube_service = YouTubeService.from_oauth_tokens(
            access_token=access_token,
            refresh_token=refresh_token,
        )
        
        # Fetch video details for metadata
        try:
            video_info = youtube_service.get_video_details(video_id)
            if video_info:
                scan.video_title = video_info.title
                scan.video_thumbnail = video_info.thumbnail_url
                scan.channel_name = video_info.channel_name
                db.commit()
        except YouTubeAPIError as e:
            logger.warning(f"Failed to fetch video details: {e}")
            # Continue without video details
        
        # Fetch all comments (Requirement 3.2)
        try:
            comments = youtube_service.get_all_comments(video_id)
        except YouTubeAPIError as e:
            scan.status = "failed"
            scan.error_message = f"YouTube API error: {e.message}"
            db.commit()
            
            # Retry on quota exceeded
            if e.reason == "quotaExceeded":
                raise self.retry(countdown=300, exc=e)
            
            return {"error": str(e)}
        
        if not comments:
            # No comments to process
            scan.status = "completed"
            scan.total_comments = 0
            scan.gambling_count = 0
            scan.clean_count = 0
            scan.scanned_at = datetime.now(timezone.utc)
            db.commit()
            return {
                "scan_id": scan_id,
                "total_comments": 0,
                "gambling_count": 0,
                "clean_count": 0,
            }
        
        # Initialize prediction service
        prediction_service = PredictionService()
        
        # Process comments in batches for efficiency
        batch_size = 100
        gambling_count = 0
        clean_count = 0
        total_processed = 0
        
        for i in range(0, len(comments), batch_size):
            batch = comments[i:i + batch_size]
            texts = [comment.text for comment in batch]
            
            # Run ML prediction (Requirement 3.3)
            predictions = prediction_service.predict_batch(texts)
            
            # Store results (Requirement 3.4)
            for comment, prediction in zip(batch, predictions):
                result = ScanResult(
                    scan_id=UUID(scan_id),
                    comment_id=comment.id,
                    comment_text=comment.text,
                    author_name=comment.author_name,
                    author_avatar=comment.author_avatar,
                    is_gambling=prediction["is_gambling"],
                    confidence=prediction["confidence"],
                )
                db.add(result)
                
                if prediction["is_gambling"]:
                    gambling_count += 1
                else:
                    clean_count += 1
                
                total_processed += 1
            
            # Commit batch and update progress (Requirement 9.2)
            scan.total_comments = total_processed
            scan.gambling_count = gambling_count
            scan.clean_count = clean_count
            db.commit()
            
            logger.info(
                f"Scan {scan_id}: Processed {total_processed}/{len(comments)} comments"
            )
        
        # Update final status (Requirement 3.5)
        scan.status = "completed"
        scan.total_comments = total_processed
        scan.gambling_count = gambling_count
        scan.clean_count = clean_count
        scan.scanned_at = datetime.now(timezone.utc)
        db.commit()
        
        logger.info(
            f"Scan {scan_id} completed: {total_processed} comments, "
            f"{gambling_count} gambling, {clean_count} clean"
        )
        
        return {
            "scan_id": scan_id,
            "total_comments": total_processed,
            "gambling_count": gambling_count,
            "clean_count": clean_count,
        }
        
    except Exception as e:
        logger.exception(f"Scan {scan_id} failed with error: {e}")
        
        # Update scan status to failed
        try:
            scan = db.execute(
                select(Scan).where(Scan.id == UUID(scan_id))
            ).scalar_one_or_none()
            
            if scan:
                scan.status = "failed"
                scan.error_message = str(e)
                db.commit()
        except Exception:
            pass
        
        # Retry with exponential backoff (Requirement 9.4)
        raise self.retry(exc=e)
        
    finally:
        db.close()


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def batch_predict(self, texts: list[str]) -> list[dict]:
    """
    Async batch prediction task.
    
    Processes batch predictions asynchronously for large batches.
    
    Args:
        texts: List of comment texts to classify
        
    Returns:
        List of prediction results
        
    Requirements: 2.3
    """
    from app.services.prediction_service import PredictionService
    
    try:
        prediction_service = PredictionService()
        results = prediction_service.predict_batch(texts)
        return results
    except Exception as e:
        logger.exception(f"Batch prediction failed: {e}")
        raise self.retry(exc=e)


@shared_task
def cleanup_old_results(retention_days: int = 30) -> dict:
    """
    Periodic task to clean up old scan results.
    
    Removes scan results older than the retention period to manage
    database size.
    
    Args:
        retention_days: Number of days to retain results (default: 30)
        
    Returns:
        Dictionary with cleanup statistics
        
    Requirements: 9.5
    """
    from app.models.scan import Scan
    
    db = get_sync_db()
    
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        
        # Find old scans
        old_scans = db.execute(
            select(Scan).where(Scan.created_at < cutoff_date)
        ).scalars().all()
        
        deleted_scans = 0
        deleted_results = 0
        
        for scan in old_scans:
            # Count results before deletion (cascade will handle them)
            result_count = len(scan.results)
            deleted_results += result_count
            
            db.delete(scan)
            deleted_scans += 1
        
        db.commit()
        
        logger.info(
            f"Cleanup completed: {deleted_scans} scans, "
            f"{deleted_results} results deleted"
        )
        
        return {
            "deleted_scans": deleted_scans,
            "deleted_results": deleted_results,
            "cutoff_date": cutoff_date.isoformat(),
        }
        
    except Exception as e:
        logger.exception(f"Cleanup task failed: {e}")
        db.rollback()
        raise
        
    finally:
        db.close()
