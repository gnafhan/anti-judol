"""
Property-based tests for the YouTube Service.

Tests correctness properties for video response format and bulk deletion.
"""

from datetime import datetime, timezone
from typing import Any

import pytest
from hypothesis import given, strategies as st, settings, assume

from app.schemas.youtube import VideoInfo, CommentInfo, VideoListResponse, CommentListResponse


# Custom strategies for generating valid YouTube-like data
def video_id_strategy():
    """Generate valid YouTube video ID-like strings (11 characters)."""
    return st.text(
        alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-",
        min_size=11,
        max_size=11
    )


def channel_id_strategy():
    """Generate valid YouTube channel ID-like strings."""
    return st.text(
        alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-",
        min_size=20,
        max_size=30
    )


def thumbnail_url_strategy():
    """Generate valid thumbnail URL strings."""
    return st.from_regex(
        r"https://i\.ytimg\.com/vi/[A-Za-z0-9_-]{11}/(default|medium|high)\.jpg",
        fullmatch=True
    )


def datetime_strategy():
    """Generate valid datetime objects."""
    return st.datetimes(
        min_value=datetime(2005, 1, 1),  # YouTube launch year
        max_value=datetime(2030, 12, 31),
        timezones=st.just(timezone.utc)
    )


def video_info_strategy():
    """Generate valid VideoInfo objects."""
    return st.builds(
        VideoInfo,
        id=video_id_strategy(),
        title=st.text(min_size=1, max_size=100),
        description=st.one_of(st.none(), st.text(min_size=0, max_size=500)),
        thumbnail_url=thumbnail_url_strategy(),
        channel_name=st.text(min_size=1, max_size=100),
        channel_id=channel_id_strategy(),
        view_count=st.integers(min_value=0, max_value=10_000_000_000),
        comment_count=st.integers(min_value=0, max_value=100_000_000),
        published_at=datetime_strategy(),
    )


def comment_info_strategy():
    """Generate valid CommentInfo objects."""
    return st.builds(
        CommentInfo,
        id=st.text(
            alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-",
            min_size=20,
            max_size=30
        ),
        text=st.text(min_size=1, max_size=1000),
        author_name=st.text(min_size=1, max_size=100),
        author_avatar=st.one_of(st.none(), st.from_regex(r"https://yt[0-9]\.ggpht\.com/[A-Za-z0-9_-]+", fullmatch=True)),
        author_channel_id=st.one_of(st.none(), channel_id_strategy()),
        like_count=st.integers(min_value=0, max_value=10_000_000),
        published_at=datetime_strategy(),
    )


class TestVideoResponseRequiredFields:
    """
    **Feature: gambling-comment-detector, Property 8: Video Response Required Fields**
    **Validates: Requirements 4.2, 5.2**
    
    For any video returned from my-videos or search endpoints, the response 
    SHALL contain non-null values for id, title, thumbnail_url, and channel_name.
    """
    
    @given(video=video_info_strategy())
    @settings(max_examples=100)
    def test_video_info_has_required_fields(self, video: VideoInfo):
        """VideoInfo objects always have required non-null fields."""
        # Verify required fields are non-null and non-empty
        assert video.id is not None, "Video id must not be None"
        assert video.id != "", "Video id must not be empty"
        
        assert video.title is not None, "Video title must not be None"
        assert video.title != "", "Video title must not be empty"
        
        assert video.thumbnail_url is not None, "Video thumbnail_url must not be None"
        assert video.thumbnail_url != "", "Video thumbnail_url must not be empty"
        
        assert video.channel_name is not None, "Video channel_name must not be None"
        assert video.channel_name != "", "Video channel_name must not be empty"
        
        # Verify channel_id is also present (required by schema)
        assert video.channel_id is not None, "Video channel_id must not be None"
    
    @given(
        videos=st.lists(video_info_strategy(), min_size=0, max_size=25),
        next_page_token=st.one_of(st.none(), st.text(min_size=10, max_size=50)),
        total_results=st.integers(min_value=0, max_value=1_000_000)
    )
    @settings(max_examples=100)
    def test_video_list_response_all_items_have_required_fields(
        self, videos: list[VideoInfo], next_page_token: str | None, total_results: int
    ):
        """VideoListResponse items all have required non-null fields."""
        response = VideoListResponse(
            items=videos,
            next_page_token=next_page_token,
            total_results=total_results
        )
        
        for i, video in enumerate(response.items):
            assert video.id is not None and video.id != "", \
                f"Video {i}: id must be non-null and non-empty"
            assert video.title is not None and video.title != "", \
                f"Video {i}: title must be non-null and non-empty"
            assert video.thumbnail_url is not None and video.thumbnail_url != "", \
                f"Video {i}: thumbnail_url must be non-null and non-empty"
            assert video.channel_name is not None and video.channel_name != "", \
                f"Video {i}: channel_name must be non-null and non-empty"
    
    @given(video=video_info_strategy())
    @settings(max_examples=100)
    def test_video_info_serialization_preserves_required_fields(self, video: VideoInfo):
        """VideoInfo serialization round-trip preserves required fields."""
        # Serialize to JSON
        json_str = video.model_dump_json()
        
        # Deserialize back
        restored = VideoInfo.model_validate_json(json_str)
        
        # Verify required fields are preserved
        assert restored.id == video.id, "id must be preserved after round-trip"
        assert restored.title == video.title, "title must be preserved after round-trip"
        assert restored.thumbnail_url == video.thumbnail_url, "thumbnail_url must be preserved after round-trip"
        assert restored.channel_name == video.channel_name, "channel_name must be preserved after round-trip"
        assert restored.channel_id == video.channel_id, "channel_id must be preserved after round-trip"



class TestBulkDeletionSequentialProcessing:
    """
    **Feature: gambling-comment-detector, Property 9: Bulk Deletion Sequential Processing**
    **Validates: Requirements 6.2, 12.4**
    
    For any list of comment IDs submitted for bulk deletion, the system 
    SHALL process them sequentially with minimum delay between API calls.
    """
    
    @given(
        comment_ids=st.lists(
            st.text(
                alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-",
                min_size=20,
                max_size=30
            ),
            min_size=0,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_bulk_deletion_processes_all_ids(self, comment_ids: list[str]):
        """Bulk deletion attempts to process all provided comment IDs."""
        from unittest.mock import MagicMock, patch
        from app.services.youtube_service import YouTubeService
        
        # Create a mock YouTube client
        mock_youtube = MagicMock()
        
        # Track which comment IDs were processed
        processed_ids = []
        
        def mock_delete(id):
            processed_ids.append(id)
            mock_execute = MagicMock()
            return mock_execute
        
        mock_youtube.comments.return_value.delete = mock_delete
        
        # Create service with mocked client
        with patch.object(YouTubeService, '__init__', lambda self, **kwargs: None):
            service = YouTubeService()
            service._youtube = mock_youtube
            service.BULK_OPERATION_DELAY = 0  # No delay for testing
            
            # Perform bulk deletion
            result = service.delete_comments_bulk(comment_ids, delay=0)
        
        # Verify all IDs were processed
        assert len(processed_ids) == len(comment_ids), \
            f"All {len(comment_ids)} comment IDs should be processed, but only {len(processed_ids)} were"
        
        # Verify IDs were processed in order (sequential processing)
        assert processed_ids == comment_ids, \
            "Comment IDs should be processed in the same order they were provided"
        
        # Verify result structure
        assert "deleted" in result, "Result must contain 'deleted' field"
        assert "failed" in result, "Result must contain 'failed' field"
        assert "total" in result, "Result must contain 'total' field"
        assert result["total"] == len(comment_ids), \
            f"Total should equal number of input IDs ({len(comment_ids)})"
    
    @given(
        num_ids=st.integers(min_value=2, max_value=5),
        delay=st.floats(min_value=0.01, max_value=0.1, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50)
    def test_bulk_deletion_respects_delay_between_calls(self, num_ids: int, delay: float):
        """Bulk deletion adds delay between sequential API calls."""
        import time
        from unittest.mock import MagicMock, patch
        from app.services.youtube_service import YouTubeService
        
        # Generate comment IDs
        comment_ids = [f"comment_{i}" for i in range(num_ids)]
        
        # Create a mock YouTube client
        mock_youtube = MagicMock()
        
        # Track timestamps of each call
        call_timestamps = []
        
        def mock_delete(id):
            call_timestamps.append(time.time())
            mock_execute = MagicMock()
            return mock_execute
        
        mock_youtube.comments.return_value.delete = mock_delete
        
        # Create service with mocked client
        with patch.object(YouTubeService, '__init__', lambda self, **kwargs: None):
            service = YouTubeService()
            service._youtube = mock_youtube
            service.BULK_OPERATION_DELAY = delay
            
            # Perform bulk deletion with specified delay
            service.delete_comments_bulk(comment_ids, delay=delay)
        
        # Verify delays between calls
        for i in range(1, len(call_timestamps)):
            actual_delay = call_timestamps[i] - call_timestamps[i - 1]
            # Allow some tolerance for timing variations
            assert actual_delay >= delay * 0.9, \
                f"Delay between call {i-1} and {i} should be at least {delay}s, but was {actual_delay}s"
    
    @given(
        success_ids=st.lists(
            st.text(
                alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
                min_size=10,
                max_size=20
            ),
            min_size=0,
            max_size=5
        ),
        fail_ids=st.lists(
            st.text(
                alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
                min_size=10,
                max_size=20
            ),
            min_size=0,
            max_size=5
        )
    )
    @settings(max_examples=100)
    def test_bulk_deletion_continues_after_failures(
        self, success_ids: list[str], fail_ids: list[str]
    ):
        """Bulk deletion continues processing remaining IDs after a failure."""
        from unittest.mock import MagicMock, patch
        from googleapiclient.errors import HttpError
        from app.services.youtube_service import YouTubeService
        
        # Interleave success and fail IDs
        all_ids = []
        fail_set = set(fail_ids)
        for s_id in success_ids:
            all_ids.append(s_id)
        for f_id in fail_ids:
            all_ids.append(f_id)
        
        # Create a mock YouTube client
        mock_youtube = MagicMock()
        
        processed_ids = []
        
        def mock_delete(id):
            processed_ids.append(id)
            if id in fail_set:
                # Simulate an HTTP error
                mock_resp = MagicMock()
                mock_resp.status = 403
                raise HttpError(mock_resp, b'{"error": {"message": "forbidden"}}')
            mock_execute = MagicMock()
            return mock_execute
        
        mock_youtube.comments.return_value.delete = mock_delete
        
        # Create service with mocked client
        with patch.object(YouTubeService, '__init__', lambda self, **kwargs: None):
            service = YouTubeService()
            service._youtube = mock_youtube
            service.BULK_OPERATION_DELAY = 0
            
            # Perform bulk deletion
            result = service.delete_comments_bulk(all_ids, delay=0)
        
        # Verify all IDs were attempted (processing continued after failures)
        assert len(processed_ids) == len(all_ids), \
            f"All {len(all_ids)} IDs should be attempted, but only {len(processed_ids)} were"
        
        # Verify result counts
        assert result["total"] == len(all_ids)
        assert len(result["deleted"]) + len(result["failed"]) == len(all_ids), \
            "Sum of deleted and failed should equal total"
