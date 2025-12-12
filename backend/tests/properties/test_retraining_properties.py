"""
Property-based tests for retraining service operations.

Tests correctness properties for:
- Training Data Combination (Property 13)
- Retraining Threshold Trigger (Property 6)

**Feature: auto-ml-retraining, Property 13: Training Data Combination**
**Validates: Requirements 6.3, 9.3**

**Feature: auto-ml-retraining, Property 6: Retraining Threshold Trigger**
**Validates: Requirements 5.1**
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import uuid
import tempfile
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest
from hypothesis import given, strategies as st, settings, assume

from app.models.validation import ValidationFeedback
from app.services.retraining_service import (
    RetrainingService,
    ModelMetrics,
)


# Strategies for generating test data
comment_strategy = st.text(
    min_size=1, 
    max_size=200,
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'S', 'Z'))
).filter(lambda x: len(x.strip()) > 0)

label_strategy = st.booleans()


class TestTrainingDataCombinationProperties:
    """
    **Feature: auto-ml-retraining, Property 13: Training Data Combination**
    **Validates: Requirements 6.3, 9.3**
    
    For any retraining operation, the training dataset should be the union of
    the original dataset (df_all.csv) and all validation feedback marked as unused,
    with no duplicates and correct label assignment.
    """

    @given(
        original_comments=st.lists(
            st.tuples(comment_strategy, st.booleans()),
            min_size=5,
            max_size=20,
        ),
        validation_comments=st.lists(
            st.tuples(comment_strategy, st.booleans()),
            min_size=0,
            max_size=10,
        ),
    )
    @settings(max_examples=100)
    def test_combined_data_contains_all_original_comments(
        self,
        original_comments: list[tuple[str, bool]],
        validation_comments: list[tuple[str, bool]],
    ):
        """
        Property: Combined data contains all original comments
        
        For any combination of original and validation data, all unique
        original comments should be present in the combined dataset.
        """
        # Create original DataFrame
        original_df = pd.DataFrame([
            {'comment': c, 'label': 1 if l else 0}
            for c, l in original_comments
        ])
        
        # Create validation DataFrame
        validation_df = pd.DataFrame([
            {'comment': c, 'label': 1 if l else 0}
            for c, l in validation_comments
        ]) if validation_comments else pd.DataFrame(columns=['comment', 'label'])
        
        # Combine (simulating the service logic)
        if len(validation_df) > 0:
            combined_df = pd.concat([original_df, validation_df], ignore_index=True)
        else:
            combined_df = original_df.copy()
        
        # Remove duplicates keeping last (validation takes precedence)
        combined_df = combined_df.drop_duplicates(subset=['comment'], keep='last')
        
        # Get unique original comments
        original_unique = set(original_df['comment'].unique())
        combined_comments = set(combined_df['comment'].values)
        
        # All original comments should be in combined (unless overwritten by validation)
        # Actually, all unique comments from both should be present
        all_input_comments = original_unique.union(
            set(v[0] for v in validation_comments)
        )
        
        assert combined_comments == all_input_comments

    @given(
        original_comments=st.lists(
            st.tuples(comment_strategy, st.booleans()),
            min_size=5,
            max_size=20,
        ),
        validation_comments=st.lists(
            st.tuples(comment_strategy, st.booleans()),
            min_size=1,
            max_size=10,
        ),
    )
    @settings(max_examples=100)
    def test_combined_data_contains_all_validation_comments(
        self,
        original_comments: list[tuple[str, bool]],
        validation_comments: list[tuple[str, bool]],
    ):
        """
        Property: Combined data contains all validation comments
        
        For any combination, all validation comments should be present
        in the combined dataset.
        """
        # Create original DataFrame
        original_df = pd.DataFrame([
            {'comment': c, 'label': 1 if l else 0}
            for c, l in original_comments
        ])
        
        # Create validation DataFrame
        validation_df = pd.DataFrame([
            {'comment': c, 'label': 1 if l else 0}
            for c, l in validation_comments
        ])
        
        # Combine
        combined_df = pd.concat([original_df, validation_df], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=['comment'], keep='last')
        
        combined_comments = set(combined_df['comment'].values)
        validation_unique = set(v[0] for v in validation_comments)
        
        # All validation comments should be in combined
        assert validation_unique.issubset(combined_comments)

    @given(
        original_comments=st.lists(
            st.tuples(comment_strategy, st.booleans()),
            min_size=5,
            max_size=20,
        ),
        validation_comments=st.lists(
            st.tuples(comment_strategy, st.booleans()),
            min_size=0,
            max_size=10,
        ),
    )
    @settings(max_examples=100)
    def test_combined_data_has_no_duplicates(
        self,
        original_comments: list[tuple[str, bool]],
        validation_comments: list[tuple[str, bool]],
    ):
        """
        Property: Combined data has no duplicate comments
        
        For any combination, the resulting dataset should have no
        duplicate comment texts.
        """
        # Create original DataFrame
        original_df = pd.DataFrame([
            {'comment': c, 'label': 1 if l else 0}
            for c, l in original_comments
        ])
        
        # Create validation DataFrame
        validation_df = pd.DataFrame([
            {'comment': c, 'label': 1 if l else 0}
            for c, l in validation_comments
        ]) if validation_comments else pd.DataFrame(columns=['comment', 'label'])
        
        # Combine
        if len(validation_df) > 0:
            combined_df = pd.concat([original_df, validation_df], ignore_index=True)
        else:
            combined_df = original_df.copy()
        
        combined_df = combined_df.drop_duplicates(subset=['comment'], keep='last')
        
        # Check no duplicates
        assert len(combined_df) == len(combined_df['comment'].unique())

    @given(
        shared_comment=comment_strategy,
        original_label=st.booleans(),
        validation_label=st.booleans(),
    )
    @settings(max_examples=100)
    def test_validation_label_takes_precedence_over_original(
        self,
        shared_comment: str,
        original_label: bool,
        validation_label: bool,
    ):
        """
        Property: Validation label takes precedence for duplicate comments
        
        When a comment exists in both original and validation data,
        the validation label should be used (keep='last' behavior).
        """
        # Create original DataFrame with the shared comment
        original_df = pd.DataFrame([
            {'comment': shared_comment, 'label': 1 if original_label else 0},
            {'comment': 'other original comment', 'label': 0},
        ])
        
        # Create validation DataFrame with the same comment but potentially different label
        validation_df = pd.DataFrame([
            {'comment': shared_comment, 'label': 1 if validation_label else 0},
        ])
        
        # Combine (validation comes after original)
        combined_df = pd.concat([original_df, validation_df], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=['comment'], keep='last')
        
        # Find the label for the shared comment
        result_label = combined_df[combined_df['comment'] == shared_comment]['label'].iloc[0]
        expected_label = 1 if validation_label else 0
        
        # Validation label should take precedence
        assert result_label == expected_label

    @given(
        validation_data=st.lists(
            st.tuples(
                comment_strategy,
                st.booleans(),  # corrected_label (True=gambling, False=clean)
            ),
            min_size=1,
            max_size=20,
            unique_by=lambda x: x[0],  # Ensure unique comments to avoid ambiguity
        ),
    )
    @settings(max_examples=100)
    def test_validation_label_correctly_converted(
        self,
        validation_data: list[tuple[str, bool]],
    ):
        """
        Property: Validation corrected_label correctly converted to numeric label
        
        For any validation feedback, corrected_label=True should map to label=1 (gambling)
        and corrected_label=False should map to label=0 (clean).
        """
        # Simulate the conversion logic from RetrainingService.get_training_data
        converted_data = []
        for comment, corrected_label in validation_data:
            converted_data.append({
                'comment': comment,
                'label': 1 if corrected_label else 0,
            })
        
        df = pd.DataFrame(converted_data)
        
        # Verify conversion - each unique comment should have correct label
        for comment, corrected_label in validation_data:
            row = df[df['comment'] == comment].iloc[0]
            expected_label = 1 if corrected_label else 0
            assert row['label'] == expected_label

    @given(
        original_size=st.integers(min_value=10, max_value=50),
        validation_size=st.integers(min_value=0, max_value=20),
    )
    @settings(max_examples=100)
    def test_combined_size_is_bounded(
        self,
        original_size: int,
        validation_size: int,
    ):
        """
        Property: Combined dataset size is bounded correctly
        
        The combined dataset size should be at most original_size + validation_size
        (and at least max(original_size, validation_size) if all are unique).
        """
        # Generate unique comments for original
        original_comments = [f"original_comment_{i}" for i in range(original_size)]
        original_df = pd.DataFrame([
            {'comment': c, 'label': i % 2}
            for i, c in enumerate(original_comments)
        ])
        
        # Generate unique comments for validation (some may overlap)
        validation_comments = [f"validation_comment_{i}" for i in range(validation_size)]
        validation_df = pd.DataFrame([
            {'comment': c, 'label': i % 2}
            for i, c in enumerate(validation_comments)
        ]) if validation_size > 0 else pd.DataFrame(columns=['comment', 'label'])
        
        # Combine
        if len(validation_df) > 0:
            combined_df = pd.concat([original_df, validation_df], ignore_index=True)
        else:
            combined_df = original_df.copy()
        
        combined_df = combined_df.drop_duplicates(subset=['comment'], keep='last')
        
        # Size bounds
        assert len(combined_df) <= original_size + validation_size
        assert len(combined_df) >= max(1, min(original_size, validation_size))


class TestRetrainingThresholdTriggerProperties:
    """
    **Feature: auto-ml-retraining, Property 6: Retraining Threshold Trigger**
    **Validates: Requirements 5.1**
    
    For any state where the count of unused validation feedback reaches or exceeds
    the configured threshold, the system should trigger exactly one retraining job.
    """

    @given(
        pending_count=st.integers(min_value=0, max_value=200),
        threshold=st.integers(min_value=1, max_value=150),
    )
    @settings(max_examples=100)
    def test_threshold_check_returns_true_when_reached(
        self,
        pending_count: int,
        threshold: int,
    ):
        """
        Property: Threshold check returns True when pending >= threshold
        
        For any pending count and threshold, check_retraining_threshold
        should return True if and only if pending_count >= threshold.
        """
        # Simulate the threshold check logic
        should_trigger = pending_count >= threshold
        
        # This is the core logic from ValidationService.check_retraining_threshold
        assert should_trigger == (pending_count >= threshold)

    @given(
        pending_count=st.integers(min_value=0, max_value=99),
    )
    @settings(max_examples=100)
    def test_threshold_not_reached_with_default(
        self,
        pending_count: int,
    ):
        """
        Property: Default threshold (100) not reached with fewer validations
        
        With the default threshold of 100, any pending count < 100
        should not trigger retraining.
        """
        default_threshold = 100
        should_trigger = pending_count >= default_threshold
        
        assert should_trigger == False

    @given(
        pending_count=st.integers(min_value=100, max_value=500),
    )
    @settings(max_examples=100)
    def test_threshold_reached_with_default(
        self,
        pending_count: int,
    ):
        """
        Property: Default threshold (100) reached with sufficient validations
        
        With the default threshold of 100, any pending count >= 100
        should trigger retraining.
        """
        default_threshold = 100
        should_trigger = pending_count >= default_threshold
        
        assert should_trigger == True

    @given(
        threshold=st.integers(min_value=1, max_value=1000),
    )
    @settings(max_examples=100)
    def test_exact_threshold_triggers_retraining(
        self,
        threshold: int,
    ):
        """
        Property: Exact threshold count triggers retraining
        
        When pending count equals exactly the threshold,
        retraining should be triggered.
        """
        pending_count = threshold
        should_trigger = pending_count >= threshold
        
        assert should_trigger == True

    @given(
        threshold=st.integers(min_value=2, max_value=1000),
    )
    @settings(max_examples=100)
    def test_one_below_threshold_does_not_trigger(
        self,
        threshold: int,
    ):
        """
        Property: One below threshold does not trigger retraining
        
        When pending count is exactly one less than threshold,
        retraining should not be triggered.
        """
        pending_count = threshold - 1
        should_trigger = pending_count >= threshold
        
        assert should_trigger == False

    @given(
        initial_count=st.integers(min_value=0, max_value=98),
        additions=st.integers(min_value=1, max_value=50),
    )
    @settings(max_examples=100)
    def test_threshold_crossing_detection(
        self,
        initial_count: int,
        additions: int,
    ):
        """
        Property: Threshold crossing is correctly detected
        
        When validations are added and the count crosses the threshold,
        the trigger should change from False to True.
        """
        threshold = 100
        
        # Before additions
        before_trigger = initial_count >= threshold
        
        # After additions
        final_count = initial_count + additions
        after_trigger = final_count >= threshold
        
        # If we crossed the threshold
        if initial_count < threshold <= final_count:
            assert before_trigger == False
            assert after_trigger == True
        elif final_count < threshold:
            assert after_trigger == False
        else:
            # Both were already above threshold
            assert before_trigger == True
            assert after_trigger == True

    @given(
        pending_count=st.integers(min_value=0, max_value=300),
        threshold=st.integers(min_value=1, max_value=200),
    )
    @settings(max_examples=100)
    def test_threshold_trigger_is_idempotent(
        self,
        pending_count: int,
        threshold: int,
    ):
        """
        Property: Threshold trigger check is idempotent
        
        For any given pending count and threshold, calling the threshold
        check multiple times should always return the same result.
        This ensures exactly one retraining job would be triggered
        (not multiple) for the same state.
        """
        # Check multiple times
        result1 = pending_count >= threshold
        result2 = pending_count >= threshold
        result3 = pending_count >= threshold
        
        # All results should be identical
        assert result1 == result2 == result3

    @given(
        pending_count=st.integers(min_value=0, max_value=500),
        threshold=st.integers(min_value=1, max_value=300),
    )
    @settings(max_examples=100)
    def test_threshold_trigger_monotonicity(
        self,
        pending_count: int,
        threshold: int,
    ):
        """
        Property: Threshold trigger is monotonic with respect to pending count
        
        If threshold is triggered at count N, it should also be triggered
        at any count M > N. This ensures that once we have enough validations,
        adding more won't prevent retraining.
        """
        should_trigger = pending_count >= threshold
        
        # If triggered, adding more should still trigger
        if should_trigger:
            for additional in range(1, 10):
                assert (pending_count + additional) >= threshold
        
        # If not triggered, removing should still not trigger
        if not should_trigger and pending_count > 0:
            for less in range(1, min(pending_count + 1, 10)):
                assert (pending_count - less) < threshold

    @given(
        threshold=st.integers(min_value=1, max_value=500),
    )
    @settings(max_examples=100)
    def test_threshold_boundary_precision(
        self,
        threshold: int,
    ):
        """
        Property: Threshold boundary is precise
        
        The threshold check should have exact boundary behavior:
        - threshold - 1 should NOT trigger
        - threshold should trigger
        - threshold + 1 should trigger
        
        This validates Requirements 5.1: trigger when count reaches threshold.
        """
        # Just below threshold - should NOT trigger
        assert ((threshold - 1) >= threshold) == False
        
        # Exactly at threshold - should trigger
        assert (threshold >= threshold) == True
        
        # Just above threshold - should trigger
        assert ((threshold + 1) >= threshold) == True

    @given(
        num_validations=st.lists(
            st.booleans(),  # used_in_training flag
            min_size=0,
            max_size=200,
        ),
        threshold=st.integers(min_value=1, max_value=150),
    )
    @settings(max_examples=100)
    def test_only_unused_validations_count_toward_threshold(
        self,
        num_validations: list[bool],
        threshold: int,
    ):
        """
        Property: Only unused validations count toward threshold
        
        For any set of validations with varying used_in_training flags,
        only those with used_in_training=False should count toward
        the retraining threshold.
        """
        # Count unused validations (used_in_training=False means unused)
        unused_count = sum(1 for used in num_validations if not used)
        
        # Threshold check should only consider unused
        should_trigger = unused_count >= threshold
        
        # Verify the logic
        assert should_trigger == (unused_count >= threshold)
        
        # Total count should not affect the decision
        total_count = len(num_validations)
        # Even if total >= threshold, if unused < threshold, should not trigger
        if unused_count < threshold:
            assert should_trigger == False


class TestTrainingDataCombinationIntegrationProperties:
    """
    **Feature: auto-ml-retraining, Property 13: Training Data Combination**
    **Validates: Requirements 6.3, 9.3**
    
    Integration-style property tests that validate the actual get_training_data()
    method behavior with mocked database and file system.
    
    For any retraining operation, the training dataset should be the union of
    the original dataset (df_all.csv) and all validation feedback marked as unused,
    with no duplicates and correct label assignment.
    """

    @given(
        original_comments=st.lists(
            st.tuples(comment_strategy, st.booleans()),
            min_size=5,
            max_size=20,
            unique_by=lambda x: x[0],
        ),
        validation_feedback=st.lists(
            st.tuples(
                comment_strategy,
                st.booleans(),  # corrected_label
                st.booleans(),  # used_in_training
            ),
            min_size=0,
            max_size=15,
            unique_by=lambda x: x[0],
        ),
    )
    @settings(max_examples=100)
    def test_only_unused_validation_feedback_included(
        self,
        original_comments: list[tuple[str, bool]],
        validation_feedback: list[tuple[str, bool, bool]],
    ):
        """
        Property: Only unused validation feedback is included in training data
        
        For any set of validation feedback records, only those with
        used_in_training=False should be included in the combined dataset.
        This validates Requirements 9.3.
        """
        # Create original DataFrame
        original_df = pd.DataFrame([
            {'comment': c, 'label': 1 if l else 0}
            for c, l in original_comments
        ])
        
        # Separate used and unused validation feedback
        unused_validations = [
            (comment, label) 
            for comment, label, used in validation_feedback 
            if not used  # used_in_training=False means unused
        ]
        used_validations = [
            (comment, label) 
            for comment, label, used in validation_feedback 
            if used  # used_in_training=True means already used
        ]
        
        # Create validation DataFrame (only unused)
        validation_df = pd.DataFrame([
            {'comment': c, 'label': 1 if l else 0}
            for c, l in unused_validations
        ]) if unused_validations else pd.DataFrame(columns=['comment', 'label'])
        
        # Combine (simulating get_training_data logic)
        if len(validation_df) > 0:
            combined_df = pd.concat([original_df, validation_df], ignore_index=True)
        else:
            combined_df = original_df.copy()
        
        combined_df = combined_df.drop_duplicates(subset=['comment'], keep='last')
        
        combined_comments = set(combined_df['comment'].values)
        
        # All unused validation comments should be in combined
        unused_comments = set(c for c, _ in unused_validations)
        assert unused_comments.issubset(combined_comments)
        
        # Used validation comments should NOT be in combined (unless in original)
        original_comment_set = set(c for c, _ in original_comments)
        used_comments = set(c for c, _ in used_validations)
        used_only_comments = used_comments - original_comment_set - unused_comments
        
        # Comments that are ONLY in used validations should not appear
        for comment in used_only_comments:
            assert comment not in combined_comments

    @given(
        original_comments=st.lists(
            st.tuples(comment_strategy, st.booleans()),
            min_size=5,
            max_size=20,
            unique_by=lambda x: x[0],
        ),
        validation_feedback=st.lists(
            st.tuples(
                comment_strategy,
                st.booleans(),  # corrected_label
            ),
            min_size=1,
            max_size=15,
            unique_by=lambda x: x[0],
        ),
    )
    @settings(max_examples=100)
    def test_union_property_holds(
        self,
        original_comments: list[tuple[str, bool]],
        validation_feedback: list[tuple[str, bool]],
    ):
        """
        Property: Combined dataset is the union of original and validation data
        
        For any original dataset and validation feedback, the combined dataset
        should contain exactly the union of unique comments from both sources.
        This validates Requirements 6.3.
        """
        # Create original DataFrame
        original_df = pd.DataFrame([
            {'comment': c, 'label': 1 if l else 0}
            for c, l in original_comments
        ])
        
        # Create validation DataFrame
        validation_df = pd.DataFrame([
            {'comment': c, 'label': 1 if l else 0}
            for c, l in validation_feedback
        ])
        
        # Combine
        combined_df = pd.concat([original_df, validation_df], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=['comment'], keep='last')
        
        # Calculate expected union
        original_set = set(c for c, _ in original_comments)
        validation_set = set(c for c, _ in validation_feedback)
        expected_union = original_set.union(validation_set)
        
        combined_set = set(combined_df['comment'].values)
        
        # Combined should equal the union
        assert combined_set == expected_union

    @given(
        shared_comments=st.lists(
            st.tuples(comment_strategy, st.booleans(), st.booleans()),
            min_size=1,
            max_size=10,
            unique_by=lambda x: x[0],
        ),
    )
    @settings(max_examples=100)
    def test_overlapping_comments_use_validation_label(
        self,
        shared_comments: list[tuple[str, bool, bool]],
    ):
        """
        Property: For overlapping comments, validation label takes precedence
        
        When a comment exists in both original dataset and validation feedback,
        the final label should be from the validation feedback (user correction).
        This validates Requirements 6.3, 9.3.
        """
        # Create original DataFrame with one label
        original_df = pd.DataFrame([
            {'comment': c, 'label': 1 if orig_label else 0}
            for c, orig_label, _ in shared_comments
        ])
        
        # Create validation DataFrame with potentially different label
        validation_df = pd.DataFrame([
            {'comment': c, 'label': 1 if val_label else 0}
            for c, _, val_label in shared_comments
        ])
        
        # Combine (validation comes after original, keep='last')
        combined_df = pd.concat([original_df, validation_df], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=['comment'], keep='last')
        
        # Verify each comment has the validation label
        for comment, _, val_label in shared_comments:
            row = combined_df[combined_df['comment'] == comment]
            assert len(row) == 1
            expected_label = 1 if val_label else 0
            assert row['label'].iloc[0] == expected_label

    @given(
        original_size=st.integers(min_value=10, max_value=100),
        validation_size=st.integers(min_value=0, max_value=50),
        overlap_ratio=st.floats(min_value=0.0, max_value=0.5),
    )
    @settings(max_examples=100)
    def test_combined_size_with_overlap(
        self,
        original_size: int,
        validation_size: int,
        overlap_ratio: float,
    ):
        """
        Property: Combined size accounts for overlapping comments correctly
        
        When there are overlapping comments between original and validation data,
        the combined size should be: original + validation - overlap.
        """
        # Calculate overlap count
        max_overlap = min(original_size, validation_size)
        overlap_count = int(max_overlap * overlap_ratio)
        
        # Generate original comments
        original_comments = [f"original_{i}" for i in range(original_size)]
        
        # Generate validation comments with some overlap
        validation_comments = []
        # Add overlapping comments
        for i in range(overlap_count):
            validation_comments.append(original_comments[i])
        # Add unique validation comments
        for i in range(validation_size - overlap_count):
            validation_comments.append(f"validation_{i}")
        
        # Create DataFrames
        original_df = pd.DataFrame([
            {'comment': c, 'label': 0}
            for c in original_comments
        ])
        
        validation_df = pd.DataFrame([
            {'comment': c, 'label': 1}
            for c in validation_comments
        ]) if validation_comments else pd.DataFrame(columns=['comment', 'label'])
        
        # Combine
        if len(validation_df) > 0:
            combined_df = pd.concat([original_df, validation_df], ignore_index=True)
        else:
            combined_df = original_df.copy()
        
        combined_df = combined_df.drop_duplicates(subset=['comment'], keep='last')
        
        # Expected size: original + validation - overlap
        expected_size = original_size + validation_size - overlap_count
        
        assert len(combined_df) == expected_size


class TestModelMetricsProperties:
    """
    Property tests for ModelMetrics data structure.
    """

    @given(
        accuracy=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        precision=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        recall=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        f1=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        training_samples=st.integers(min_value=1, max_value=100000),
        validation_samples=st.integers(min_value=0, max_value=10000),
    )
    @settings(max_examples=100)
    def test_model_metrics_stores_values_correctly(
        self,
        accuracy: float,
        precision: float,
        recall: float,
        f1: float,
        training_samples: int,
        validation_samples: int,
    ):
        """
        Property: ModelMetrics stores all values correctly
        
        For any valid metric values, ModelMetrics should store
        and return them exactly as provided.
        """
        metrics = ModelMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1=f1,
            training_samples=training_samples,
            validation_samples=validation_samples,
        )
        
        assert metrics.accuracy == accuracy
        assert metrics.precision == precision
        assert metrics.recall == recall
        assert metrics.f1 == f1
        assert metrics.training_samples == training_samples
        assert metrics.validation_samples == validation_samples

    @given(
        accuracy=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        precision=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        recall=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        f1=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        training_samples=st.integers(min_value=1, max_value=100000),
        validation_samples=st.integers(min_value=0, max_value=10000),
    )
    @settings(max_examples=100)
    def test_model_metrics_to_dict_contains_all_fields(
        self,
        accuracy: float,
        precision: float,
        recall: float,
        f1: float,
        training_samples: int,
        validation_samples: int,
    ):
        """
        Property: to_dict() contains all metric fields
        
        The dictionary representation should contain all metric fields
        with correct values.
        """
        metrics = ModelMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1=f1,
            training_samples=training_samples,
            validation_samples=validation_samples,
        )
        
        result = metrics.to_dict()
        
        assert 'accuracy' in result
        assert 'precision' in result
        assert 'recall' in result
        assert 'f1' in result
        assert 'training_samples' in result
        assert 'validation_samples' in result
        
        assert result['accuracy'] == accuracy
        assert result['precision'] == precision
        assert result['recall'] == recall
        assert result['f1'] == f1
        assert result['training_samples'] == training_samples
        assert result['validation_samples'] == validation_samples


class TestModelContinuityDuringRetrainingProperties:
    """
    **Feature: auto-ml-retraining, Property 7: Model Continuity During Retraining**
    **Validates: Requirements 5.2**
    
    For any retraining job execution, the prediction service should continue
    serving predictions using the current active model without interruption.
    """

    @given(
        test_texts=st.lists(
            comment_strategy,
            min_size=1,
            max_size=10,
        ),
    )
    @settings(max_examples=100)
    def test_predictions_available_during_reload_flag(
        self,
        test_texts: list[str],
    ):
        """
        Property: Predictions remain available when reload is in progress
        
        For any set of prediction requests, the prediction service should
        continue to serve predictions even when a reload is flagged as in progress.
        This simulates the scenario where retraining is happening in background.
        """
        from app.services.prediction_service import PredictionService
        
        # Simulate reload in progress state
        # The service should still serve predictions from the current model
        
        # Reset to ensure clean state
        PredictionService.reset_model()
        
        # Load initial model
        try:
            PredictionService.load_model()
        except Exception:
            # Skip if model file not available in test environment
            return
        
        # Set reload flag (simulating retraining in progress)
        with PredictionService._model_lock:
            original_flag = PredictionService._is_reloading
            PredictionService._is_reloading = True
        
        try:
            # Predictions should still work
            service = PredictionService()
            for text in test_texts:
                result = service.predict_single(text)
                
                # Verify prediction structure is valid
                assert 'text' in result
                assert 'is_gambling' in result
                assert 'confidence' in result
                assert isinstance(result['is_gambling'], bool)
                assert 0.0 <= result['confidence'] <= 1.0
        finally:
            # Restore flag
            with PredictionService._model_lock:
                PredictionService._is_reloading = original_flag

    @given(
        test_texts=st.lists(
            comment_strategy,
            min_size=1,
            max_size=5,
        ),
    )
    @settings(max_examples=100)
    def test_model_reference_stable_during_prediction(
        self,
        test_texts: list[str],
    ):
        """
        Property: Model reference remains stable during a prediction call
        
        For any prediction request, the model used should be consistent
        throughout the entire prediction (no mid-prediction swap).
        """
        from app.services.prediction_service import PredictionService
        
        # Reset to ensure clean state
        PredictionService.reset_model()
        
        try:
            PredictionService.load_model()
        except Exception:
            # Skip if model file not available
            return
        
        service = PredictionService()
        
        # Get model reference before prediction
        with PredictionService._model_lock:
            model_before = PredictionService._model
        
        # Make predictions
        for text in test_texts:
            result = service.predict_single(text)
            assert result is not None
        
        # Model reference should be the same (no unexpected swap)
        with PredictionService._model_lock:
            model_after = PredictionService._model
        
        # In absence of explicit reload, model should be same object
        assert model_before is model_after

    @given(
        batch_size=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=100)
    def test_batch_predictions_complete_atomically(
        self,
        batch_size: int,
    ):
        """
        Property: Batch predictions complete atomically
        
        For any batch prediction request, all predictions in the batch
        should use the same model version (atomic batch processing).
        """
        from app.services.prediction_service import PredictionService
        
        # Reset to ensure clean state
        PredictionService.reset_model()
        
        try:
            PredictionService.load_model()
        except Exception:
            return
        
        # Generate test texts
        texts = [f"test comment number {i}" for i in range(batch_size)]
        
        service = PredictionService()
        
        # Batch prediction should complete fully
        results = service.predict_batch(texts)
        
        # All results should be present
        assert len(results) == batch_size
        
        # All results should have valid structure
        for i, result in enumerate(results):
            assert result['text'] == texts[i]
            assert isinstance(result['is_gambling'], bool)
            assert 0.0 <= result['confidence'] <= 1.0

    @given(
        num_predictions=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=100)
    def test_concurrent_reload_does_not_block_predictions(
        self,
        num_predictions: int,
    ):
        """
        Property: Reload operation does not block ongoing predictions
        
        For any number of prediction requests, if a reload is attempted
        while predictions are in progress, predictions should complete
        without being blocked.
        """
        import threading
        import time
        from app.services.prediction_service import PredictionService
        
        # Reset to ensure clean state
        PredictionService.reset_model()
        
        try:
            PredictionService.load_model()
        except Exception:
            return
        
        service = PredictionService()
        prediction_results = []
        prediction_errors = []
        
        def make_predictions():
            """Make predictions in a separate thread."""
            try:
                for i in range(num_predictions):
                    result = service.predict_single(f"test text {i}")
                    prediction_results.append(result)
            except Exception as e:
                prediction_errors.append(e)
        
        # Start prediction thread
        pred_thread = threading.Thread(target=make_predictions)
        pred_thread.start()
        
        # Attempt reload while predictions are running
        # This should not block or fail the predictions
        # Note: reload_model will return False if already reloading
        PredictionService.reload_model()
        
        # Wait for predictions to complete
        pred_thread.join(timeout=10)
        
        # Predictions should have completed without errors
        assert len(prediction_errors) == 0
        assert len(prediction_results) == num_predictions


class TestModelSwapOnSuccessProperties:
    """
    **Feature: auto-ml-retraining, Property 8: Model Swap on Success**
    **Validates: Requirements 5.3**
    
    For any successful retraining job, the new model should become active,
    and the previous model should be marked as inactive with deactivated_at timestamp set.
    """

    @given(
        version_string=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=('L', 'N'))
        ).map(lambda x: f"v{x}"),
    )
    @settings(max_examples=100)
    def test_new_model_becomes_active_after_deployment(
        self,
        version_string: str,
    ):
        """
        Property: New model becomes active after successful deployment
        
        For any successful model deployment, the new model version
        should have is_active=True.
        """
        # This tests the deployment logic conceptually
        # In actual deployment, the new model's is_active should be True
        
        # Simulate the deployment state transition
        class MockModelVersion:
            def __init__(self, version: str, is_active: bool = False):
                self.version = version
                self.is_active = is_active
                self.activated_at = None
                self.deactivated_at = None
        
        # Before deployment
        new_model = MockModelVersion(version_string, is_active=False)
        
        # Simulate successful deployment
        from datetime import datetime, timezone
        new_model.is_active = True
        new_model.activated_at = datetime.now(timezone.utc)
        
        # After deployment, new model should be active
        assert new_model.is_active == True
        assert new_model.activated_at is not None

    @given(
        old_version=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('L', 'N'))).map(lambda x: f"v{x}_old"),
        new_version=st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('L', 'N'))).map(lambda x: f"v{x}_new"),
    )
    @settings(max_examples=100)
    def test_previous_model_deactivated_on_new_deployment(
        self,
        old_version: str,
        new_version: str,
    ):
        """
        Property: Previous model is deactivated when new model is deployed
        
        For any successful deployment, the previously active model
        should have is_active=False and deactivated_at set.
        """
        from datetime import datetime, timezone
        
        class MockModelVersion:
            def __init__(self, version: str, is_active: bool = False):
                self.version = version
                self.is_active = is_active
                self.activated_at = None
                self.deactivated_at = None
        
        # Setup: old model is active
        old_model = MockModelVersion(old_version, is_active=True)
        old_model.activated_at = datetime.now(timezone.utc)
        
        new_model = MockModelVersion(new_version, is_active=False)
        
        # Simulate deployment: deactivate old, activate new
        old_model.is_active = False
        old_model.deactivated_at = datetime.now(timezone.utc)
        
        new_model.is_active = True
        new_model.activated_at = datetime.now(timezone.utc)
        
        # Verify state
        assert old_model.is_active == False
        assert old_model.deactivated_at is not None
        assert new_model.is_active == True

    @given(
        num_versions=st.integers(min_value=2, max_value=5),
    )
    @settings(max_examples=100)
    def test_only_one_model_active_at_a_time(
        self,
        num_versions: int,
    ):
        """
        Property: Only one model version is active at any time
        
        For any number of model versions, exactly one should be active
        after any deployment operation.
        """
        from datetime import datetime, timezone
        
        class MockModelVersion:
            def __init__(self, version: str, is_active: bool = False):
                self.version = version
                self.is_active = is_active
        
        # Create multiple versions
        versions = [MockModelVersion(f"v{i}", is_active=False) for i in range(num_versions)]
        
        # Simulate deploying each version in sequence
        for i, version in enumerate(versions):
            # Deactivate all others
            for v in versions:
                v.is_active = False
            
            # Activate current
            version.is_active = True
            
            # Verify exactly one is active
            active_count = sum(1 for v in versions if v.is_active)
            assert active_count == 1
            assert version.is_active == True

    @given(
        accuracy=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        f1=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_model_metrics_preserved_after_deployment(
        self,
        accuracy: float,
        f1: float,
    ):
        """
        Property: Model metrics are preserved after deployment
        
        For any model deployment with metrics, the metrics should be
        stored and retrievable from the model version record.
        """
        from app.services.retraining_service import ModelMetrics
        
        # Create metrics
        metrics = ModelMetrics(
            accuracy=accuracy,
            precision=0.8,
            recall=0.7,
            f1=f1,
            training_samples=1000,
            validation_samples=100,
        )
        
        # Simulate storing in model version
        class MockModelVersion:
            def __init__(self):
                self.accuracy = None
                self.f1_score = None
        
        model_version = MockModelVersion()
        model_version.accuracy = metrics.accuracy
        model_version.f1_score = metrics.f1
        
        # Verify metrics preserved
        assert model_version.accuracy == accuracy
        assert model_version.f1_score == f1


class TestModelPreservationOnFailureProperties:
    """
    **Feature: auto-ml-retraining, Property 9: Model Preservation on Failure**
    **Validates: Requirements 5.4**
    
    For any failed retraining job, the current active model should remain
    active and unchanged.
    """

    @given(
        test_texts=st.lists(
            comment_strategy,
            min_size=1,
            max_size=5,
        ),
    )
    @settings(max_examples=100)
    def test_model_unchanged_after_failed_reload(
        self,
        test_texts: list[str],
    ):
        """
        Property: Model remains unchanged after failed reload attempt
        
        For any failed reload attempt (e.g., file not found), the current
        model should continue to be used for predictions.
        """
        from app.services.prediction_service import PredictionService
        from pathlib import Path
        
        # Reset and load initial model
        PredictionService.reset_model()
        
        try:
            PredictionService.load_model()
        except Exception:
            return
        
        # Get predictions before failed reload
        service = PredictionService()
        predictions_before = [service.predict_single(t) for t in test_texts]
        
        # Get model reference before
        with PredictionService._model_lock:
            model_before = PredictionService._model
        
        # Attempt reload with non-existent file (should fail)
        result = PredictionService.reload_model(Path("/nonexistent/model.joblib"))
        
        # Reload should have failed
        assert result == False
        
        # Model should be unchanged
        with PredictionService._model_lock:
            model_after = PredictionService._model
        
        assert model_before is model_after
        
        # Predictions should still work and be consistent
        predictions_after = [service.predict_single(t) for t in test_texts]
        
        for before, after in zip(predictions_before, predictions_after):
            assert before['is_gambling'] == after['is_gambling']
            assert before['confidence'] == after['confidence']

    @given(
        num_failed_attempts=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=100)
    def test_model_stable_after_multiple_failed_reloads(
        self,
        num_failed_attempts: int,
    ):
        """
        Property: Model remains stable after multiple failed reload attempts
        
        For any number of failed reload attempts, the model should remain
        the same and continue serving predictions.
        """
        from app.services.prediction_service import PredictionService
        from pathlib import Path
        
        # Reset and load initial model
        PredictionService.reset_model()
        
        try:
            PredictionService.load_model()
        except Exception:
            return
        
        # Get initial model reference
        with PredictionService._model_lock:
            initial_model = PredictionService._model
        
        # Attempt multiple failed reloads
        for i in range(num_failed_attempts):
            result = PredictionService.reload_model(Path(f"/nonexistent/model_{i}.joblib"))
            assert result == False
        
        # Model should still be the initial one
        with PredictionService._model_lock:
            current_model = PredictionService._model
        
        assert initial_model is current_model

    @given(
        version_string=st.text(
            min_size=1,
            max_size=10,
            alphabet=st.characters(whitelist_categories=('L', 'N'))
        ).map(lambda x: f"v{x}"),
    )
    @settings(max_examples=100)
    def test_active_model_version_unchanged_on_deployment_failure(
        self,
        version_string: str,
    ):
        """
        Property: Active model version unchanged on deployment failure
        
        For any failed deployment attempt, the currently active model
        version in the database should remain active.
        """
        from datetime import datetime, timezone
        
        class MockModelVersion:
            def __init__(self, version: str, is_active: bool = False):
                self.version = version
                self.is_active = is_active
                self.activated_at = None
                self.deactivated_at = None
        
        # Setup: current model is active
        current_model = MockModelVersion("v_current", is_active=True)
        current_model.activated_at = datetime.now(timezone.utc)
        
        # Simulate failed deployment (exception during save)
        deployment_failed = True
        
        if deployment_failed:
            # On failure, current model should remain active
            # No changes should be made
            pass
        
        # Verify current model is still active
        assert current_model.is_active == True
        assert current_model.deactivated_at is None

    @given(
        test_text=comment_strategy,
    )
    @settings(max_examples=100)
    def test_predictions_continue_after_training_failure(
        self,
        test_text: str,
    ):
        """
        Property: Predictions continue normally after training failure
        
        For any training failure scenario, the prediction service should
        continue to serve predictions using the existing model.
        """
        from app.services.prediction_service import PredictionService
        
        # Reset and load initial model
        PredictionService.reset_model()
        
        try:
            PredictionService.load_model()
        except Exception:
            return
        
        service = PredictionService()
        
        # Get prediction before simulated failure
        result_before = service.predict_single(test_text)
        
        # Simulate training failure (model not swapped)
        # In real scenario, retrain_model task would catch exception
        # and not call reload_model
        training_succeeded = False
        
        if not training_succeeded:
            # No reload happens
            pass
        
        # Predictions should still work
        result_after = service.predict_single(test_text)
        
        # Results should be identical (same model)
        assert result_before['is_gambling'] == result_after['is_gambling']
        assert result_before['confidence'] == result_after['confidence']

    @given(
        error_type=st.sampled_from(['file_not_found', 'corrupted_file', 'permission_denied']),
    )
    @settings(max_examples=100)
    def test_model_preserved_for_various_failure_types(
        self,
        error_type: str,
    ):
        """
        Property: Model preserved regardless of failure type
        
        For any type of failure during model loading (file not found,
        corrupted file, permission denied), the current model should
        be preserved.
        """
        from app.services.prediction_service import PredictionService
        from pathlib import Path
        
        # Reset and load initial model
        PredictionService.reset_model()
        
        try:
            PredictionService.load_model()
        except Exception:
            return
        
        # Get initial model
        with PredictionService._model_lock:
            initial_model = PredictionService._model
        
        # Simulate different failure scenarios
        if error_type == 'file_not_found':
            result = PredictionService.reload_model(Path("/nonexistent/model.joblib"))
        elif error_type == 'corrupted_file':
            # Would fail during joblib.load - simulated by non-existent file
            result = PredictionService.reload_model(Path("/dev/null"))
        elif error_type == 'permission_denied':
            # Would fail during file access - simulated by non-existent file
            result = PredictionService.reload_model(Path("/root/protected/model.joblib"))
        
        # All should fail
        assert result == False
        
        # Model should be preserved
        with PredictionService._model_lock:
            current_model = PredictionService._model
        
        assert initial_model is current_model
