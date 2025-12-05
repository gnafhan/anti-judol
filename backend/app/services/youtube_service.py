"""
YouTube service for interacting with YouTube Data API v3.

This service provides:
- YouTube API client initialization with OAuth or API key
- Video fetching (user's videos and public search)
- Comment fetching with pagination
- Comment deletion with rate limiting

Requirements: 3.2, 4.1, 4.2, 4.4, 5.1, 5.2, 6.1, 6.2, 6.3, 12.4
"""

import time
from datetime import datetime
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import get_settings
from app.schemas.youtube import (
    VideoInfo,
    CommentInfo,
    VideoListResponse,
    CommentListResponse,
)

settings = get_settings()


class YouTubeAPIError(Exception):
    """Raised when YouTube API operations fail."""
    
    def __init__(self, status_code: int, message: str, reason: str = ""):
        self.status_code = status_code
        self.message = message
        self.reason = reason
        super().__init__(f"YouTube API Error ({status_code}): {message}")


class YouTubeService:
    """
    YouTube service for interacting with YouTube Data API v3.
    
    Supports both OAuth credentials (for user's own videos/comments)
    and API key (for public video search).
    
    Implements:
    - Video fetching (Requirements 4.1, 4.2, 4.4, 5.1, 5.2)
    - Comment fetching (Requirements 3.2)
    - Comment deletion (Requirements 6.1, 6.2, 6.3, 12.4)
    """
    
    # Rate limiting delay between bulk operations (in seconds)
    BULK_OPERATION_DELAY = 0.5
    
    def __init__(
        self,
        credentials: Credentials | None = None,
        api_key: str | None = None
    ):
        """
        Initialize YouTube API client.
        
        Args:
            credentials: OAuth2 credentials for authenticated user operations
            api_key: API key for public operations (search, public video info)
            
        At least one of credentials or api_key must be provided.
        If both are provided, credentials take precedence for authenticated operations.
        
        Requirements: 4.1, 5.1
        """
        self._credentials = credentials
        self._api_key = api_key or settings.youtube_api_key
        
        # Build the YouTube client
        if credentials:
            self._youtube = build("youtube", "v3", credentials=credentials)
        elif self._api_key:
            self._youtube = build("youtube", "v3", developerKey=self._api_key)
        else:
            raise ValueError(
                "Either OAuth credentials or API key must be provided"
            )
    
    @classmethod
    def from_oauth_tokens(
        cls,
        access_token: str,
        refresh_token: str | None = None,
        token_uri: str = "https://oauth2.googleapis.com/token"
    ) -> "YouTubeService":
        """
        Create YouTubeService from OAuth tokens.
        
        Args:
            access_token: OAuth access token
            refresh_token: OAuth refresh token (optional)
            token_uri: Token refresh URI
            
        Returns:
            YouTubeService instance with OAuth credentials
        """
        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=token_uri,
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
        )
        return cls(credentials=credentials)
    
    @classmethod
    def from_api_key(cls, api_key: str | None = None) -> "YouTubeService":
        """
        Create YouTubeService using API key only.
        
        Args:
            api_key: YouTube API key (uses settings if not provided)
            
        Returns:
            YouTubeService instance with API key authentication
        """
        return cls(api_key=api_key or settings.youtube_api_key)


    def _handle_http_error(self, error: HttpError) -> None:
        """
        Convert HttpError to YouTubeAPIError with appropriate details.
        
        Args:
            error: The HttpError from YouTube API
            
        Raises:
            YouTubeAPIError: With status code, message, and reason
        """
        status_code = error.resp.status
        
        # Try to extract error details from response
        try:
            error_details = error.error_details[0] if error.error_details else {}
            reason = error_details.get("reason", "")
            message = error_details.get("message", str(error))
        except (IndexError, AttributeError):
            reason = ""
            message = str(error)
        
        raise YouTubeAPIError(status_code, message, reason)
    
    def _parse_video_item(self, item: dict[str, Any]) -> VideoInfo:
        """
        Parse a YouTube API video item into VideoInfo schema.
        
        Args:
            item: Raw video item from YouTube API response
            
        Returns:
            VideoInfo object with parsed data
        """
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        thumbnails = snippet.get("thumbnails", {})
        
        # Get best available thumbnail
        thumbnail_url = ""
        for quality in ["high", "medium", "default"]:
            if quality in thumbnails:
                thumbnail_url = thumbnails[quality].get("url", "")
                break
        
        # Parse published date
        published_str = snippet.get("publishedAt", "")
        try:
            published_at = datetime.fromisoformat(
                published_str.replace("Z", "+00:00")
            )
        except (ValueError, AttributeError):
            published_at = datetime.utcnow()
        
        return VideoInfo(
            id=item.get("id", ""),
            title=snippet.get("title", ""),
            description=snippet.get("description"),
            thumbnail_url=thumbnail_url,
            channel_name=snippet.get("channelTitle", ""),
            channel_id=snippet.get("channelId", ""),
            view_count=int(statistics.get("viewCount", 0)),
            comment_count=int(statistics.get("commentCount", 0)),
            published_at=published_at,
        )
    
    def _parse_search_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """
        Parse a YouTube API search result item.
        
        Search results have a different structure than video list results.
        
        Args:
            item: Raw search result item from YouTube API
            
        Returns:
            Dictionary with video ID and snippet data
        """
        snippet = item.get("snippet", {})
        video_id = item.get("id", {}).get("videoId", "")
        thumbnails = snippet.get("thumbnails", {})
        
        # Get best available thumbnail
        thumbnail_url = ""
        for quality in ["high", "medium", "default"]:
            if quality in thumbnails:
                thumbnail_url = thumbnails[quality].get("url", "")
                break
        
        # Parse published date
        published_str = snippet.get("publishedAt", "")
        try:
            published_at = datetime.fromisoformat(
                published_str.replace("Z", "+00:00")
            )
        except (ValueError, AttributeError):
            published_at = datetime.utcnow()
        
        return {
            "id": video_id,
            "title": snippet.get("title", ""),
            "description": snippet.get("description"),
            "thumbnail_url": thumbnail_url,
            "channel_name": snippet.get("channelTitle", ""),
            "channel_id": snippet.get("channelId", ""),
            "published_at": published_at,
        }
    
    def get_my_videos(
        self,
        page_token: str | None = None,
        max_results: int = 25
    ) -> VideoListResponse:
        """
        Get authenticated user's uploaded videos.
        
        Requires OAuth credentials with youtube.readonly scope.
        
        Args:
            page_token: Token for pagination (from previous response)
            max_results: Maximum number of videos to return (1-50)
            
        Returns:
            VideoListResponse with user's videos
            
        Raises:
            YouTubeAPIError: If API call fails
            
        Requirements: 4.1, 4.4
        """
        try:
            # First, get the user's channel
            channels_response = self._youtube.channels().list(
                part="contentDetails",
                mine=True
            ).execute()
            
            if not channels_response.get("items"):
                return VideoListResponse(items=[], total_results=0)
            
            # Get the uploads playlist ID
            uploads_playlist_id = (
                channels_response["items"][0]
                .get("contentDetails", {})
                .get("relatedPlaylists", {})
                .get("uploads")
            )
            
            if not uploads_playlist_id:
                return VideoListResponse(items=[], total_results=0)
            
            # Get videos from uploads playlist
            request_params = {
                "part": "snippet",
                "playlistId": uploads_playlist_id,
                "maxResults": min(max_results, 50),
            }
            if page_token:
                request_params["pageToken"] = page_token
            
            playlist_response = self._youtube.playlistItems().list(
                **request_params
            ).execute()
            
            # Get video IDs for statistics
            video_ids = [
                item.get("snippet", {}).get("resourceId", {}).get("videoId")
                for item in playlist_response.get("items", [])
                if item.get("snippet", {}).get("resourceId", {}).get("videoId")
            ]
            
            if not video_ids:
                return VideoListResponse(
                    items=[],
                    next_page_token=playlist_response.get("nextPageToken"),
                    total_results=playlist_response.get("pageInfo", {}).get("totalResults", 0),
                )
            
            # Get full video details with statistics
            videos_response = self._youtube.videos().list(
                part="snippet,statistics",
                id=",".join(video_ids)
            ).execute()
            
            videos = [
                self._parse_video_item(item)
                for item in videos_response.get("items", [])
            ]
            
            return VideoListResponse(
                items=videos,
                next_page_token=playlist_response.get("nextPageToken"),
                total_results=playlist_response.get("pageInfo", {}).get("totalResults", 0),
            )
            
        except HttpError as e:
            self._handle_http_error(e)


    def search_videos(
        self,
        query: str,
        page_token: str | None = None,
        max_results: int = 25
    ) -> VideoListResponse:
        """
        Search for public YouTube videos.
        
        Can be used with either OAuth credentials or API key.
        
        Args:
            query: Search query string
            page_token: Token for pagination (from previous response)
            max_results: Maximum number of videos to return (1-50)
            
        Returns:
            VideoListResponse with search results
            
        Raises:
            YouTubeAPIError: If API call fails
            
        Requirements: 5.1, 5.2
        """
        try:
            request_params = {
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": min(max_results, 50),
            }
            if page_token:
                request_params["pageToken"] = page_token
            
            search_response = self._youtube.search().list(
                **request_params
            ).execute()
            
            # Parse search results to get video IDs
            search_items = [
                self._parse_search_item(item)
                for item in search_response.get("items", [])
                if item.get("id", {}).get("videoId")
            ]
            
            if not search_items:
                return VideoListResponse(
                    items=[],
                    next_page_token=search_response.get("nextPageToken"),
                    total_results=search_response.get("pageInfo", {}).get("totalResults", 0),
                )
            
            # Get full video details with statistics
            video_ids = [item["id"] for item in search_items]
            videos_response = self._youtube.videos().list(
                part="snippet,statistics",
                id=",".join(video_ids)
            ).execute()
            
            videos = [
                self._parse_video_item(item)
                for item in videos_response.get("items", [])
            ]
            
            return VideoListResponse(
                items=videos,
                next_page_token=search_response.get("nextPageToken"),
                total_results=search_response.get("pageInfo", {}).get("totalResults", 0),
            )
            
        except HttpError as e:
            self._handle_http_error(e)
    
    def get_video_details(self, video_id: str) -> VideoInfo | None:
        """
        Get details for a single video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            VideoInfo object or None if video not found
            
        Raises:
            YouTubeAPIError: If API call fails
            
        Requirements: 4.2
        """
        try:
            response = self._youtube.videos().list(
                part="snippet,statistics",
                id=video_id
            ).execute()
            
            items = response.get("items", [])
            if not items:
                return None
            
            return self._parse_video_item(items[0])
            
        except HttpError as e:
            self._handle_http_error(e)


    def _parse_comment_item(self, item: dict[str, Any]) -> CommentInfo:
        """
        Parse a YouTube API comment item into CommentInfo schema.
        
        Args:
            item: Raw comment item from YouTube API response
            
        Returns:
            CommentInfo object with parsed data
        """
        # Handle both top-level comments and comment thread items
        if "snippet" in item and "topLevelComment" in item.get("snippet", {}):
            # This is a comment thread item
            comment_data = item["snippet"]["topLevelComment"]["snippet"]
            comment_id = item["snippet"]["topLevelComment"]["id"]
        elif "snippet" in item:
            # This is a direct comment item
            comment_data = item["snippet"]
            comment_id = item["id"]
        else:
            comment_data = {}
            comment_id = item.get("id", "")
        
        # Parse published date
        published_str = comment_data.get("publishedAt", "")
        try:
            published_at = datetime.fromisoformat(
                published_str.replace("Z", "+00:00")
            )
        except (ValueError, AttributeError):
            published_at = datetime.utcnow()
        
        return CommentInfo(
            id=comment_id,
            text=comment_data.get("textDisplay", ""),
            author_name=comment_data.get("authorDisplayName", ""),
            author_avatar=comment_data.get("authorProfileImageUrl"),
            author_channel_id=comment_data.get("authorChannelId", {}).get("value"),
            like_count=int(comment_data.get("likeCount", 0)),
            published_at=published_at,
        )
    
    def get_comments(
        self,
        video_id: str,
        page_token: str | None = None,
        max_results: int = 100
    ) -> CommentListResponse:
        """
        Get comments for a video with pagination.
        
        Args:
            video_id: YouTube video ID
            page_token: Token for pagination (from previous response)
            max_results: Maximum number of comments to return (1-100)
            
        Returns:
            CommentListResponse with video comments
            
        Raises:
            YouTubeAPIError: If API call fails
            
        Requirements: 3.2
        """
        try:
            request_params = {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": min(max_results, 100),
                "textFormat": "plainText",
            }
            if page_token:
                request_params["pageToken"] = page_token
            
            response = self._youtube.commentThreads().list(
                **request_params
            ).execute()
            
            comments = [
                self._parse_comment_item(item)
                for item in response.get("items", [])
            ]
            
            return CommentListResponse(
                items=comments,
                next_page_token=response.get("nextPageToken"),
                total_results=response.get("pageInfo", {}).get("totalResults", 0),
            )
            
        except HttpError as e:
            self._handle_http_error(e)
    
    def get_all_comments(self, video_id: str) -> list[CommentInfo]:
        """
        Fetch all comments for a video (handles pagination automatically).
        
        Warning: This may make multiple API calls for videos with many comments.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            List of all CommentInfo objects for the video
            
        Raises:
            YouTubeAPIError: If API call fails
            
        Requirements: 3.2
        """
        all_comments: list[CommentInfo] = []
        page_token: str | None = None
        
        while True:
            response = self.get_comments(
                video_id=video_id,
                page_token=page_token,
                max_results=100
            )
            
            all_comments.extend(response.items)
            
            page_token = response.next_page_token
            if not page_token:
                break
            
            # Small delay between pages to be respectful of rate limits
            time.sleep(0.1)
        
        return all_comments


    def delete_comment(self, comment_id: str) -> bool:
        """
        Delete a single comment.
        
        Requires OAuth credentials with youtube.force-ssl scope.
        The authenticated user must own the comment or the video.
        
        Args:
            comment_id: YouTube comment ID to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            YouTubeAPIError: If deletion fails (permission error, not found, etc.)
            
        Requirements: 6.1, 6.3
        """
        try:
            self._youtube.comments().delete(id=comment_id).execute()
            return True
            
        except HttpError as e:
            self._handle_http_error(e)
    
    def delete_comments_bulk(
        self,
        comment_ids: list[str],
        delay: float | None = None
    ) -> dict[str, Any]:
        """
        Delete multiple comments with rate limiting.
        
        Processes comments sequentially with delays between API calls
        to respect rate limits.
        
        Args:
            comment_ids: List of YouTube comment IDs to delete
            delay: Delay between deletions in seconds (default: BULK_OPERATION_DELAY)
            
        Returns:
            Dictionary with:
            - deleted: List of successfully deleted comment IDs
            - failed: List of dicts with comment_id and error for failed deletions
            - total: Total number of comments processed
            
        Requirements: 6.2, 12.4
        """
        if delay is None:
            delay = self.BULK_OPERATION_DELAY
        
        deleted: list[str] = []
        failed: list[dict[str, Any]] = []
        
        for i, comment_id in enumerate(comment_ids):
            try:
                self.delete_comment(comment_id)
                deleted.append(comment_id)
            except YouTubeAPIError as e:
                failed.append({
                    "comment_id": comment_id,
                    "error": e.message,
                    "reason": e.reason,
                    "status_code": e.status_code,
                })
            
            # Add delay between operations (except after the last one)
            if i < len(comment_ids) - 1 and delay > 0:
                time.sleep(delay)
        
        return {
            "deleted": deleted,
            "failed": failed,
            "total": len(comment_ids),
        }
