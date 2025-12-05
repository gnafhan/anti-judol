"""
Property-based tests for input validation enforcement.

**Feature: gambling-comment-detector, Property 17: Input Validation Enforcement**
**Validates: Requirements 11.4, 11.5**

For any request with invalid or malformed data according to Pydantic schemas,
the system SHALL return 422 status with validation error details.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from pydantic import ValidationError

from app.schemas.user import UserBase, UserResponse, TokenResponse
from app.schemas.scan import ScanCreate, ScanResponse, ScanResultResponse
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.schemas.youtube import VideoInfo, CommentInfo


class TestInputValidationProperties:
    """
    **Feature: gambling-comment-detector, Property 17: Input Validation Enforcement**
    **Validates: Requirements 11.4, 11.5**
    """

    @given(email=st.text(min_size=1, max_size=50).filter(lambda x: "@" not in x or "." not in x.split("@")[-1] if "@" in x else True))
    @settings(max_examples=100)
    def test_user_base_rejects_invalid_email(self, email: str):
        """UserBase schema SHALL reject invalid email formats."""
        # Skip valid-looking emails
        if "@" in email and "." in email.split("@")[-1] and len(email.split("@")) == 2:
            return
        
        with pytest.raises(ValidationError) as exc_info:
            UserBase(email=email)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("email" in str(e.get("loc", [])) for e in errors)

    @given(confidence=st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x < 0.0 or x > 1.0))
    @settings(max_examples=100)
    def test_prediction_response_rejects_out_of_bounds_confidence(self, confidence: float):
        """PredictionResponse schema SHALL reject confidence values outside [0.0, 1.0]."""
        with pytest.raises(ValidationError) as exc_info:
            PredictionResponse(
                text="test comment",
                is_gambling=True,
                confidence=confidence
            )
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("confidence" in str(e.get("loc", [])) for e in errors)

    @given(
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        text=st.text(min_size=1, max_size=100),
        is_gambling=st.booleans()
    )
    @settings(max_examples=100)
    def test_prediction_response_accepts_valid_confidence(self, confidence: float, text: str, is_gambling: bool):
        """PredictionResponse schema SHALL accept confidence values within [0.0, 1.0]."""
        response = PredictionResponse(
            text=text,
            is_gambling=is_gambling,
            confidence=confidence
        )
        assert response.confidence >= 0.0
        assert response.confidence <= 1.0
        assert response.text == text
        assert response.is_gambling == is_gambling

    def test_prediction_request_rejects_too_many_texts(self):
        """PredictionRequest schema SHALL reject more than 1000 texts."""
        # Test with exactly 1001 texts (boundary condition)
        texts = ["test"] * 1001
        with pytest.raises(ValidationError) as exc_info:
            PredictionRequest(texts=texts)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_prediction_request_rejects_empty_texts_list(self):
        """PredictionRequest schema SHALL reject empty texts list."""
        with pytest.raises(ValidationError) as exc_info:
            PredictionRequest(texts=[])
        
        errors = exc_info.value.errors()
        assert len(errors) > 0

    @given(texts=st.lists(st.text(min_size=1), min_size=1, max_size=1000))
    @settings(max_examples=100)
    def test_prediction_request_accepts_valid_texts(self, texts: list[str]):
        """PredictionRequest schema SHALL accept 1-1000 texts."""
        request = PredictionRequest(texts=texts)
        assert len(request.texts) == len(texts)
        assert request.texts == texts

    @given(
        video_id=st.text(min_size=1, max_size=50),
        video_url=st.one_of(st.none(), st.text(min_size=1, max_size=200))
    )
    @settings(max_examples=100)
    def test_scan_create_accepts_valid_input(self, video_id: str, video_url: str | None):
        """ScanCreate schema SHALL accept valid video_id with optional video_url."""
        scan = ScanCreate(video_id=video_id, video_url=video_url)
        assert scan.video_id == video_id
        assert scan.video_url == video_url

    @given(
        view_count=st.integers(),
        comment_count=st.integers()
    )
    @settings(max_examples=100)
    def test_video_info_requires_all_fields(self, view_count: int, comment_count: int):
        """VideoInfo schema SHALL require all mandatory fields."""
        # Missing required fields should raise ValidationError
        with pytest.raises(ValidationError):
            VideoInfo(
                id="test_id",
                # Missing title, thumbnail_url, channel_name, channel_id, published_at
                view_count=view_count,
                comment_count=comment_count
            )

    @given(like_count=st.integers())
    @settings(max_examples=100)
    def test_comment_info_requires_all_fields(self, like_count: int):
        """CommentInfo schema SHALL require all mandatory fields."""
        # Missing required fields should raise ValidationError
        with pytest.raises(ValidationError):
            CommentInfo(
                id="test_id",
                # Missing text, author_name, published_at
                like_count=like_count
            )
