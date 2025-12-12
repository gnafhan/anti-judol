"""
Property-based tests for low confidence highlighting.

Tests correctness properties for:
- Low Confidence Highlighting (Property 2)
- Filter Correctness (Property 3)

**Feature: auto-ml-retraining, Property 2: Low Confidence Highlighting**
**Validates: Requirements 3.1**

**Feature: auto-ml-retraining, Property 3: Filter Correctness**
**Validates: Requirements 3.2**
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import uuid
from typing import List

import pytest
from hypothesis import given, strategies as st, settings, assume

# Low confidence threshold (70%) - matches frontend constant
LOW_CONFIDENCE_THRESHOLD = 0.7


def is_low_confidence_result(confidence: float) -> bool:
    """
    Check if a result has low confidence.
    
    Requirements: 3.1 - Highlight comments with confidence below 70%
    
    This function mirrors the frontend implementation for testing purposes.
    """
    return confidence < LOW_CONFIDENCE_THRESHOLD


def filter_by_low_confidence(results: List[dict]) -> List[dict]:
    """
    Filter results to only include low confidence items.
    
    Requirements: 3.2 - Filter comments with confidence < 70%
    
    This function mirrors the frontend filter implementation.
    """
    return [r for r in results if is_low_confidence_result(r['confidence'])]


class TestLowConfidenceHighlightingProperties:
    """
    **Feature: auto-ml-retraining, Property 2: Low Confidence Highlighting**
    **Validates: Requirements 3.1**
    
    For any scan result with confidence score below 70% (0.7), the system
    should apply the low-confidence visual indicator. Conversely, results
    with confidence >= 70% should not have this indicator.
    """

    @given(
        confidence=st.floats(min_value=0.0, max_value=0.6999, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_below_threshold_is_low_confidence(
        self,
        confidence: float,
    ):
        """
        Property: Confidence below 70% is marked as low confidence
        
        For any confidence score strictly below 0.7, the result should
        be identified as low confidence.
        """
        assert is_low_confidence_result(confidence) == True

    @given(
        confidence=st.floats(min_value=0.7, max_value=1.0, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_at_or_above_threshold_is_not_low_confidence(
        self,
        confidence: float,
    ):
        """
        Property: Confidence at or above 70% is NOT marked as low confidence
        
        For any confidence score >= 0.7, the result should NOT be
        identified as low confidence.
        """
        assert is_low_confidence_result(confidence) == False

    @given(
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_low_confidence_is_mutually_exclusive(
        self,
        confidence: float,
    ):
        """
        Property: Low confidence classification is mutually exclusive
        
        For any confidence score, a result is either low confidence OR
        not low confidence, never both or neither.
        """
        is_low = is_low_confidence_result(confidence)
        
        # Must be exactly one of True or False
        assert is_low in [True, False]
        
        # Verify consistency with threshold
        if confidence < LOW_CONFIDENCE_THRESHOLD:
            assert is_low == True
        else:
            assert is_low == False

    @given(
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_low_confidence_deterministic(
        self,
        confidence: float,
    ):
        """
        Property: Low confidence check is deterministic
        
        For any given confidence score, calling is_low_confidence_result
        multiple times should always return the same result.
        """
        result1 = is_low_confidence_result(confidence)
        result2 = is_low_confidence_result(confidence)
        result3 = is_low_confidence_result(confidence)
        
        assert result1 == result2 == result3

    @given(
        low_confidence=st.floats(min_value=0.0, max_value=0.6999, allow_nan=False),
        high_confidence=st.floats(min_value=0.7, max_value=1.0, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_low_confidence_ordering(
        self,
        low_confidence: float,
        high_confidence: float,
    ):
        """
        Property: Lower confidence values are more likely to be low confidence
        
        If confidence_a < confidence_b and confidence_b is low confidence,
        then confidence_a must also be low confidence.
        """
        # If high_confidence is NOT low confidence (which it shouldn't be)
        # and low_confidence IS low confidence (which it should be)
        # then low_confidence < high_confidence
        
        is_low_low = is_low_confidence_result(low_confidence)
        is_low_high = is_low_confidence_result(high_confidence)
        
        # Low confidence value should be marked as low confidence
        assert is_low_low == True
        # High confidence value should NOT be marked as low confidence
        assert is_low_high == False
        # The actual values should maintain the ordering
        assert low_confidence < high_confidence


class TestFilterCorrectnessProperties:
    """
    **Feature: auto-ml-retraining, Property 3: Filter Correctness**
    **Validates: Requirements 3.2**
    
    For any filter application (e.g., "Low Confidence" filter with threshold T),
    all displayed results should satisfy the filter condition (confidence < T),
    and no results violating the condition should be displayed.
    """

    @given(
        confidences=st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
            min_size=0,
            max_size=50,
        ),
    )
    @settings(max_examples=100)
    def test_filter_only_returns_low_confidence(
        self,
        confidences: List[float],
    ):
        """
        Property: Filter only returns low confidence results
        
        All results returned by the low confidence filter should have
        confidence < 0.7.
        """
        # Create mock results
        results = [
            {'id': str(uuid.uuid4()), 'confidence': c}
            for c in confidences
        ]
        
        # Apply filter
        filtered = filter_by_low_confidence(results)
        
        # All filtered results should be low confidence
        for result in filtered:
            assert result['confidence'] < LOW_CONFIDENCE_THRESHOLD

    @given(
        confidences=st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
            min_size=0,
            max_size=50,
        ),
    )
    @settings(max_examples=100)
    def test_filter_excludes_high_confidence(
        self,
        confidences: List[float],
    ):
        """
        Property: Filter excludes high confidence results
        
        No results with confidence >= 0.7 should appear in the filtered list.
        """
        # Create mock results
        results = [
            {'id': str(uuid.uuid4()), 'confidence': c}
            for c in confidences
        ]
        
        # Apply filter
        filtered = filter_by_low_confidence(results)
        filtered_ids = {r['id'] for r in filtered}
        
        # Check that high confidence results are excluded
        for result in results:
            if result['confidence'] >= LOW_CONFIDENCE_THRESHOLD:
                assert result['id'] not in filtered_ids

    @given(
        confidences=st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
            min_size=0,
            max_size=50,
        ),
    )
    @settings(max_examples=100)
    def test_filter_includes_all_low_confidence(
        self,
        confidences: List[float],
    ):
        """
        Property: Filter includes ALL low confidence results
        
        Every result with confidence < 0.7 should appear in the filtered list.
        """
        # Create mock results
        results = [
            {'id': str(uuid.uuid4()), 'confidence': c}
            for c in confidences
        ]
        
        # Apply filter
        filtered = filter_by_low_confidence(results)
        filtered_ids = {r['id'] for r in filtered}
        
        # Check that all low confidence results are included
        for result in results:
            if result['confidence'] < LOW_CONFIDENCE_THRESHOLD:
                assert result['id'] in filtered_ids

    @given(
        confidences=st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
            min_size=0,
            max_size=50,
        ),
    )
    @settings(max_examples=100)
    def test_filter_count_matches_low_confidence_count(
        self,
        confidences: List[float],
    ):
        """
        Property: Filtered count equals low confidence count
        
        The number of filtered results should equal the number of
        results with confidence < 0.7.
        """
        # Create mock results
        results = [
            {'id': str(uuid.uuid4()), 'confidence': c}
            for c in confidences
        ]
        
        # Apply filter
        filtered = filter_by_low_confidence(results)
        
        # Count low confidence results manually
        expected_count = sum(1 for c in confidences if c < LOW_CONFIDENCE_THRESHOLD)
        
        assert len(filtered) == expected_count

    @given(
        confidences=st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
            min_size=0,
            max_size=50,
        ),
    )
    @settings(max_examples=100)
    def test_filter_preserves_result_data(
        self,
        confidences: List[float],
    ):
        """
        Property: Filter preserves result data integrity
        
        Filtered results should have the same data as the original results.
        """
        # Create mock results with additional data
        results = [
            {
                'id': str(uuid.uuid4()),
                'confidence': c,
                'comment_text': f'Comment {i}',
                'is_gambling': i % 2 == 0,
            }
            for i, c in enumerate(confidences)
        ]
        
        # Apply filter
        filtered = filter_by_low_confidence(results)
        
        # Create lookup for original results
        original_by_id = {r['id']: r for r in results}
        
        # Verify data integrity
        for result in filtered:
            original = original_by_id[result['id']]
            assert result['confidence'] == original['confidence']
            assert result['comment_text'] == original['comment_text']
            assert result['is_gambling'] == original['is_gambling']

    @given(
        confidences=st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
            min_size=0,
            max_size=50,
        ),
    )
    @settings(max_examples=100)
    def test_filter_idempotent(
        self,
        confidences: List[float],
    ):
        """
        Property: Filtering is idempotent
        
        Applying the filter twice should produce the same result as
        applying it once.
        """
        # Create mock results
        results = [
            {'id': str(uuid.uuid4()), 'confidence': c}
            for c in confidences
        ]
        
        # Apply filter once
        filtered_once = filter_by_low_confidence(results)
        
        # Apply filter again
        filtered_twice = filter_by_low_confidence(filtered_once)
        
        # Results should be identical
        assert len(filtered_once) == len(filtered_twice)
        
        once_ids = {r['id'] for r in filtered_once}
        twice_ids = {r['id'] for r in filtered_twice}
        assert once_ids == twice_ids

    @given(
        confidences=st.lists(
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
            min_size=0,
            max_size=50,
        ),
    )
    @settings(max_examples=100)
    def test_filter_subset_of_original(
        self,
        confidences: List[float],
    ):
        """
        Property: Filtered results are a subset of original
        
        Every result in the filtered list should exist in the original list.
        """
        # Create mock results
        results = [
            {'id': str(uuid.uuid4()), 'confidence': c}
            for c in confidences
        ]
        
        # Apply filter
        filtered = filter_by_low_confidence(results)
        
        # Get IDs
        original_ids = {r['id'] for r in results}
        filtered_ids = {r['id'] for r in filtered}
        
        # Filtered should be subset of original
        assert filtered_ids.issubset(original_ids)

    def test_empty_list_returns_empty(self):
        """
        Property: Empty input returns empty output
        
        Filtering an empty list should return an empty list.
        """
        results = []
        filtered = filter_by_low_confidence(results)
        assert filtered == []

    @given(
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_single_item_filter(
        self,
        confidence: float,
    ):
        """
        Property: Single item filtering works correctly
        
        A single-item list should be filtered correctly based on confidence.
        """
        results = [{'id': 'test-id', 'confidence': confidence}]
        filtered = filter_by_low_confidence(results)
        
        if confidence < LOW_CONFIDENCE_THRESHOLD:
            assert len(filtered) == 1
            assert filtered[0]['id'] == 'test-id'
        else:
            assert len(filtered) == 0
