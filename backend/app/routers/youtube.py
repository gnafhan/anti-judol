"""
YouTube Router for YouTube API operations.

Endpoints:
- GET /api/youtube/my-videos - Get authenticated user's videos
- GET /api/youtube/search - Search public videos
- GET /api/youtube/videos/{video_id} - Get single video details
- GET /api/youtube/videos/{video_id}/comments - Get video comments with pagination
- DELETE /api/youtube/comments/{comment_id} - Delete single comment
- DELETE /api/youtube/comments/bulk - Delete multiple comments with rate limiting

Requirements: 3.2, 4.1, 4.2, 4.4, 5.1, 5.2, 6.1, 6.2, 6.3, 6.4, 12.4
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.youtube import (
    VideoInfo,
    VideoListResponse,
    CommentListResponse,
)
from app.services.auth_service import (
    AuthService,
    get_current_user,
)
from app.services.youtube_service import YouTubeService, YouTubeAPIError

router = APIRouter(prefix="/api/youtube", tags=["youtube"])


def _get_youtube_service_for_user(user: User) -> YouTubeService:
    """
    Create a YouTubeService instance with the user's OAuth credentials.
    
    Args:
        user: The authenticated user with stored OAuth tokens
        
    Returns:
        YouTubeService instance configured with user's credentials
        
    Raises:
        HTTPException: If user has no valid OAuth tokens
    """
    if not user.access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "No OAuth Token",
                "error_code": "no_oauth_token",
                "message": "User has no stored OAuth access token. Please re-authenticate.",
            },
        )
    
    auth_service = AuthService()
    
    try:
        # Decrypt the stored access token
        access_token = auth_service.decrypt_token(user.access_token)
        
        # Decrypt refresh token if available
        refresh_token = None
        if user.refresh_token:
            refresh_token = auth_service.decrypt_token(user.refresh_token)
        
        # Create YouTube service with OAuth credentials
        return YouTubeService.from_oauth_tokens(
            access_token=access_token,
            refresh_token=refresh_token,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Token Error",
                "error_code": "token_error",
                "message": f"Failed to initialize YouTube service: {str(e)}",
            },
        )


def _handle_youtube_api_error(error: YouTubeAPIError) -> None:
    """
    Convert YouTubeAPIError to appropriate HTTPException.
    
    Args:
        error: The YouTubeAPIError from YouTube service
        
    Raises:
        HTTPException: With appropriate status code and error details
    """
    # Map YouTube API error reasons to HTTP status codes
    status_code_map = {
        403: status.HTTP_403_FORBIDDEN,
        404: status.HTTP_404_NOT_FOUND,
        429: status.HTTP_429_TOO_MANY_REQUESTS,
        400: status.HTTP_400_BAD_REQUEST,
    }
    
    http_status = status_code_map.get(
        error.status_code, 
        status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    
    # Special handling for quota exceeded
    if error.reason == "quotaExceeded":
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Quota Exceeded",
                "error_code": "quota_exceeded",
                "message": "YouTube API quota exceeded. Please try again later.",
            },
            headers={"Retry-After": "300"},  # 5 minutes
        )
    
    # Special handling for permission errors (Requirement 6.4)
    if error.reason == "forbidden" or error.status_code == 403:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Permission Denied",
                "error_code": "permission_denied",
                "message": "You don't have permission to perform this action. "
                          "You can only delete comments on videos you own.",
            },
        )
    
    raise HTTPException(
        status_code=http_status,
        detail={
            "error": "YouTube API Error",
            "error_code": "youtube_api_error",
            "message": error.message,
            "details": {"reason": error.reason} if error.reason else None,
        },
    )


@router.get("/my-videos", response_model=VideoListResponse)
async def get_my_videos(
    page_token: str | None = Query(None, description="Pagination token"),
    max_results: int = Query(25, ge=1, le=50, description="Max results per page"),
    current_user: User = Depends(get_current_user),
) -> VideoListResponse:
    """
    Get authenticated user's uploaded videos.
    
    Fetches videos from the user's YouTube channel using their OAuth credentials.
    Supports pagination with pageToken parameter.
    
    Requirements: 4.1, 4.4
    """
    youtube_service = _get_youtube_service_for_user(current_user)
    
    try:
        return youtube_service.get_my_videos(
            page_token=page_token,
            max_results=max_results,
        )
    except YouTubeAPIError as e:
        _handle_youtube_api_error(e)



@router.get("/search", response_model=VideoListResponse)
async def search_videos(
    q: str = Query(..., min_length=1, description="Search query"),
    page_token: str | None = Query(None, description="Pagination token"),
    max_results: int = Query(25, ge=1, le=50, description="Max results per page"),
) -> VideoListResponse:
    """
    Search for public YouTube videos.
    
    Searches YouTube for videos matching the query string.
    Does not require authentication - uses API key.
    
    Requirements: 5.1, 5.2
    """
    try:
        # Use API key for public search (no auth required)
        youtube_service = YouTubeService.from_api_key()
        
        return youtube_service.search_videos(
            query=q,
            page_token=page_token,
            max_results=max_results,
        )
    except YouTubeAPIError as e:
        _handle_youtube_api_error(e)


@router.get("/videos/{video_id}", response_model=VideoInfo)
async def get_video(
    video_id: str,
) -> VideoInfo:
    """
    Get details for a single video.
    
    Fetches video metadata including title, thumbnail, view count, etc.
    Does not require authentication - uses API key.
    
    Requirements: 4.2
    """
    try:
        # Use API key for public video info
        youtube_service = YouTubeService.from_api_key()
        
        video = youtube_service.get_video_details(video_id)
        
        if video is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Video Not Found",
                    "error_code": "video_not_found",
                    "message": f"Video with ID '{video_id}' not found",
                },
            )
        
        return video
    except YouTubeAPIError as e:
        _handle_youtube_api_error(e)


@router.get("/videos/{video_id}/comments", response_model=CommentListResponse)
async def get_video_comments(
    video_id: str,
    page_token: str | None = Query(None, description="Pagination token"),
    max_results: int = Query(100, ge=1, le=100, description="Max results per page"),
) -> CommentListResponse:
    """
    Get comments for a video with pagination.
    
    Fetches comments from a YouTube video. Supports pagination.
    Does not require authentication - uses API key.
    
    Requirements: 3.2
    """
    try:
        # Use API key for public comment fetching
        youtube_service = YouTubeService.from_api_key()
        
        return youtube_service.get_comments(
            video_id=video_id,
            page_token=page_token,
            max_results=max_results,
        )
    except YouTubeAPIError as e:
        _handle_youtube_api_error(e)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a single comment.
    
    Deletes a comment from YouTube. The authenticated user must own
    the comment or the video the comment is on.
    
    Requirements: 6.1, 6.3, 6.4
    """
    youtube_service = _get_youtube_service_for_user(current_user)
    
    try:
        youtube_service.delete_comment(comment_id)
    except YouTubeAPIError as e:
        _handle_youtube_api_error(e)


@router.delete("/comments/bulk")
async def delete_comments_bulk(
    comment_ids: list[str],
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Delete multiple comments with rate limiting.
    
    Deletes multiple comments sequentially with delays between API calls
    to respect rate limits. Returns a summary of successful and failed deletions.
    
    Requirements: 6.2, 12.4
    """
    if not comment_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid Request",
                "error_code": "empty_comment_ids",
                "message": "At least one comment ID is required",
            },
        )
    
    youtube_service = _get_youtube_service_for_user(current_user)
    
    try:
        result = youtube_service.delete_comments_bulk(comment_ids)
        
        return {
            "deleted": result["deleted"],
            "failed": result["failed"],
            "total": result["total"],
            "success_count": len(result["deleted"]),
            "failure_count": len(result["failed"]),
        }
    except YouTubeAPIError as e:
        _handle_youtube_api_error(e)
