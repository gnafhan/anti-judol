"""
Property-based tests for threshold progress notification.

Tests correctness properties for:
- Threshold Progress Notification (Property 15)

**Feature: auto-ml-retraining, Property 15: Threshold Progress Notification**
**Validates: Requirements 4.3**
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from hypothesis import given, strategies as st, settings, assume


def should_show_threshold_notification(progress: float) -> bool:
    """
    Python implementation of the threshold notification logic.
    
    Mirrors the frontend function shouldShowThresholdNotification.
    Returns True when progress reaches 80% or more of the retraining threshold.
    
    Requirements: 4.3 - Show message when count reaches 80% or more
    """
    return progress >= 80


def get_motivational_message(progress: float) -> str | None:
    """
    Python implementation of the motivational message logic.
    
    Mirrors the frontend function getMotivationalMessage.
    Returns a motivational message based on threshold progress.
    
    Requirements: 4.3 - Display motivational message near threshold
    """
    if progress >= 100:
        return '🎉 Threshold reached! Model retraining will begin soon.'
    if progress >= 90:
        return '🔥 Almost there! Just a few more validations to improve the model.'
    if progress >= 80:
        return '💪 Great progress! Your validations are making a difference.'
    if progress >= 50:
        return '📈 Halfway there! Keep validating to help improve accuracy.'
    return None


class TestThresholdProgressNotificationProperties:
    """
    **Feature: auto-ml-retraining, Property 15: Threshold Progress Notification**
    **Validates: Requirements 4.3**
    
    For any validation count that reaches 80% or more of the retraining threshold,
    the system should display a motivational/progress message to the user.
    """

    @given(
        progress=st.floats(min_value=80.0, max_value=200.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_notification_shown_at_or_above_80_percent(
        self,
        progress: float,
    ):
        """
        Property: Notification is shown when progress >= 80%
        
        For any progress value at or above 80%, the threshold notification
        should be displayed.
        """
        result = should_show_threshold_notification(progress)
        
        # Verify notification is shown
        assert result is True, f"Expected notification to be shown at {progress}%"

    @given(
        progress=st.floats(min_value=0.0, max_value=79.99, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_notification_not_shown_below_80_percent(
        self,
        progress: float,
    ):
        """
        Property: Notification is NOT shown when progress < 80%
        
        For any progress value below 80%, the threshold notification
        should NOT be displayed.
        """
        result = should_show_threshold_notification(progress)
        
        # Verify notification is not shown
        assert result is False, f"Expected notification to NOT be shown at {progress}%"

    @given(
        progress=st.floats(min_value=0.0, max_value=200.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_notification_threshold_boundary(
        self,
        progress: float,
    ):
        """
        Property: Notification threshold is exactly 80%
        
        For any progress value, the notification should be shown if and only if
        progress >= 80.
        """
        result = should_show_threshold_notification(progress)
        expected = progress >= 80
        
        assert result == expected, f"Expected {expected} at {progress}%, got {result}"

    @given(
        progress=st.floats(min_value=80.0, max_value=200.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_motivational_message_present_at_threshold(
        self,
        progress: float,
    ):
        """
        Property: Motivational message is present when notification is shown
        
        For any progress value at or above 80%, a motivational message
        should be available to display.
        """
        notification_shown = should_show_threshold_notification(progress)
        message = get_motivational_message(progress)
        
        # When notification is shown, message should be present
        assert notification_shown is True
        assert message is not None, f"Expected motivational message at {progress}%"

    @given(
        progress=st.floats(min_value=0.0, max_value=49.99, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_no_message_below_50_percent(
        self,
        progress: float,
    ):
        """
        Property: No motivational message below 50%
        
        For any progress value below 50%, no motivational message
        should be displayed.
        """
        message = get_motivational_message(progress)
        
        assert message is None, f"Expected no message at {progress}%, got: {message}"

    @given(
        progress=st.floats(min_value=50.0, max_value=79.99, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_message_present_between_50_and_80_percent(
        self,
        progress: float,
    ):
        """
        Property: Motivational message present between 50-80%
        
        For any progress value between 50% and 80%, a motivational message
        should be present (but threshold notification is not shown).
        """
        notification_shown = should_show_threshold_notification(progress)
        message = get_motivational_message(progress)
        
        # Notification not shown, but message is present
        assert notification_shown is False
        assert message is not None, f"Expected motivational message at {progress}%"
        assert message == '📈 Halfway there! Keep validating to help improve accuracy.'

    @given(
        progress=st.floats(min_value=80.0, max_value=89.99, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_correct_message_at_80_percent_tier(
        self,
        progress: float,
    ):
        """
        Property: Correct message at 80-90% tier
        
        For any progress value between 80% and 90%, the correct
        motivational message should be displayed.
        """
        message = get_motivational_message(progress)
        
        assert message == '💪 Great progress! Your validations are making a difference.'

    @given(
        progress=st.floats(min_value=90.0, max_value=99.99, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_correct_message_at_90_percent_tier(
        self,
        progress: float,
    ):
        """
        Property: Correct message at 90-100% tier
        
        For any progress value between 90% and 100%, the correct
        motivational message should be displayed.
        """
        message = get_motivational_message(progress)
        
        assert message == '🔥 Almost there! Just a few more validations to improve the model.'

    @given(
        progress=st.floats(min_value=100.0, max_value=200.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_correct_message_at_100_percent_or_above(
        self,
        progress: float,
    ):
        """
        Property: Correct message at 100%+ tier
        
        For any progress value at or above 100%, the threshold reached
        message should be displayed.
        """
        message = get_motivational_message(progress)
        
        assert message == '🎉 Threshold reached! Model retraining will begin soon.'

    @given(
        validated_count=st.integers(min_value=0, max_value=1000),
        threshold=st.integers(min_value=1, max_value=500),
    )
    @settings(max_examples=100)
    def test_progress_calculation_consistency(
        self,
        validated_count: int,
        threshold: int,
    ):
        """
        Property: Progress calculation is consistent
        
        For any validated count and threshold, the progress percentage
        should be calculated correctly and notification shown appropriately.
        """
        # Calculate progress as done in the frontend
        progress = (validated_count / threshold) * 100
        
        notification_shown = should_show_threshold_notification(progress)
        
        # Verify consistency
        if validated_count >= threshold * 0.8:
            assert notification_shown is True, \
                f"Expected notification at {validated_count}/{threshold} ({progress}%)"
        else:
            assert notification_shown is False, \
                f"Expected no notification at {validated_count}/{threshold} ({progress}%)"

    @given(
        # Use multiples of 5 to ensure clean 80% calculations (80% of 5n = 4n)
        threshold=st.integers(min_value=1, max_value=100).map(lambda x: x * 5),
    )
    @settings(max_examples=100)
    def test_exact_80_percent_boundary(
        self,
        threshold: int,
    ):
        """
        Property: Exact 80% boundary triggers notification
        
        For any threshold that is a multiple of 5, exactly 80% of that threshold
        should trigger the notification.
        
        Note: We use multiples of 5 because 80% of 5n = 4n (always an integer),
        ensuring we can test the exact 80% boundary without rounding issues.
        """
        # Calculate exactly 80% of threshold (always integer for multiples of 5)
        validated_count = int(threshold * 0.8)
        progress = (validated_count / threshold) * 100
        
        notification_shown = should_show_threshold_notification(progress)
        
        # At exactly 80%, notification should be shown
        assert notification_shown is True, \
            f"Expected notification at exactly 80% ({validated_count}/{threshold})"

    @given(
        threshold=st.integers(min_value=2, max_value=500),
    )
    @settings(max_examples=100)
    def test_just_below_80_percent_boundary(
        self,
        threshold: int,
    ):
        """
        Property: Just below 80% does NOT trigger notification
        
        For any threshold, just below 80% should NOT trigger the notification.
        """
        # Calculate just below 80% of threshold
        validated_count = int(threshold * 0.8) - 1
        if validated_count < 0:
            validated_count = 0
        progress = (validated_count / threshold) * 100
        
        # Only test if we're actually below 80%
        if progress < 80:
            notification_shown = should_show_threshold_notification(progress)
            
            assert notification_shown is False, \
                f"Expected no notification just below 80% ({validated_count}/{threshold} = {progress}%)"
