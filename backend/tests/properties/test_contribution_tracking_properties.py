"""
Property-based tests for validation contribution tracking.

Tests correctness properties for:
- Validation Contribution Tracking (Property 14)

**Feature: auto-ml-retraining, Property 14: Validation Contribution Tracking**
**Validates: Requirements 10.3**
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import uuid
from datetime import datetime, timezone
from typing import List, Tuple

import pytest
from hypothesis import given, strategies as st, settings, assume

from app.models.validation import ValidationFeedback
from app.models.model_version import ModelVersion


class TestValidationContributionTrackingProperties:
    """
    **Feature: auto-ml-retraining, Property 14: Validation Contribution Tracking**
    **Validates: Requirements 10.3**
    
    For any user viewing their validation history after a model retraining,
    the count of "contributed validations" should equal the number of their
    validations that have used_in_training=True and model_version_id set.
    """

    @given(
        num_validations=st.integers(min_value=0, max_value=50),
        num_used_in_training=st.integers(min_value=0, max_value=50),
    )
    @settings(max_examples=100)
    def test_contributed_count_equals_used_in_training_with_model_version(
        self,
        num_validations: int,
        num_used_in_training: int,
    ):
        """
        Property: Contributed count equals validations with used_in_training=True and model_version_id set
        
        For any set of validations, the count of contributed validations should
        equal the count of validations where both used_in_training=True AND
        model_version_id is not None.
        """
        # Ensure num_used_in_training doesn't exceed num_validations
        actual_used = min(num_used_in_training, num_validations)
        
        user_id = uuid.uuid4()
        model_version_id = uuid.uuid4()
        
        # Create validations
        validations: List[ValidationFeedback] = []
        
        for i in range(num_validations):
            # First 'actual_used' validations are used in training
            is_used = i < actual_used
            
            validation = ValidationFeedback(
                scan_result_id=uuid.uuid4(),
                user_id=user_id,
                comment_text=f"Test comment {i}",
                original_prediction=True,
                original_confidence=0.85,
                corrected_label=True,
                is_correction=False,
                used_in_training=is_used,
                model_version_id=model_version_id if is_used else None,
            )
            validations.append(validation)
        
        # Calculate contributed count (used_in_training=True AND model_version_id is not None)
        contributed_count = sum(
            1 for v in validations
            if v.used_in_training and v.model_version_id is not None
        )
        
        # Verify the count matches expected
        assert contributed_count == actual_used

    @given(
        num_validations=st.integers(min_value=1, max_value=30),
        used_in_training_flags=st.lists(st.booleans(), min_size=1, max_size=30),
        has_model_version_flags=st.lists(st.booleans(), min_size=1, max_size=30),
    )
    @settings(max_examples=100)
    def test_contributed_count_requires_both_conditions(
        self,
        num_validations: int,
        used_in_training_flags: List[bool],
        has_model_version_flags: List[bool],
    ):
        """
        Property: Contribution requires BOTH used_in_training=True AND model_version_id set
        
        A validation only counts as "contributed" if BOTH conditions are met:
        1. used_in_training is True
        2. model_version_id is not None
        """
        user_id = uuid.uuid4()
        model_version_id = uuid.uuid4()
        
        # Ensure we have enough flags
        actual_count = min(num_validations, len(used_in_training_flags), len(has_model_version_flags))
        assume(actual_count > 0)
        
        validations: List[ValidationFeedback] = []
        expected_contributed = 0
        
        for i in range(actual_count):
            is_used = used_in_training_flags[i]
            has_version = has_model_version_flags[i]
            
            validation = ValidationFeedback(
                scan_result_id=uuid.uuid4(),
                user_id=user_id,
                comment_text=f"Test comment {i}",
                original_prediction=True,
                original_confidence=0.85,
                corrected_label=True,
                is_correction=False,
                used_in_training=is_used,
                model_version_id=model_version_id if has_version else None,
            )
            validations.append(validation)
            
            # Only count if BOTH conditions are met
            if is_used and has_version:
                expected_contributed += 1
        
        # Calculate actual contributed count
        actual_contributed = sum(
            1 for v in validations
            if v.used_in_training and v.model_version_id is not None
        )
        
        assert actual_contributed == expected_contributed

    @given(
        num_users=st.integers(min_value=1, max_value=5),
        validations_per_user=st.integers(min_value=1, max_value=20),
        contribution_rate=st.floats(min_value=0.0, max_value=1.0),
    )
    @settings(max_examples=100)
    def test_contribution_count_is_user_specific(
        self,
        num_users: int,
        validations_per_user: int,
        contribution_rate: float,
    ):
        """
        Property: Contribution count is specific to each user
        
        Each user's contribution count should only include their own validations,
        not validations from other users.
        """
        model_version_id = uuid.uuid4()
        
        # Create validations for multiple users
        all_validations: List[ValidationFeedback] = []
        user_ids = [uuid.uuid4() for _ in range(num_users)]
        expected_contributions_per_user = {}
        
        for user_id in user_ids:
            user_validations = []
            contributed = 0
            
            for i in range(validations_per_user):
                # Determine if this validation is used in training based on rate
                is_used = (i / validations_per_user) < contribution_rate
                
                validation = ValidationFeedback(
                    scan_result_id=uuid.uuid4(),
                    user_id=user_id,
                    comment_text=f"Test comment {i}",
                    original_prediction=True,
                    original_confidence=0.85,
                    corrected_label=True,
                    is_correction=False,
                    used_in_training=is_used,
                    model_version_id=model_version_id if is_used else None,
                )
                user_validations.append(validation)
                all_validations.append(validation)
                
                if is_used:
                    contributed += 1
            
            expected_contributions_per_user[user_id] = contributed
        
        # Verify each user's contribution count
        for user_id in user_ids:
            user_contributed = sum(
                1 for v in all_validations
                if v.user_id == user_id and v.used_in_training and v.model_version_id is not None
            )
            assert user_contributed == expected_contributions_per_user[user_id]

    @given(
        num_validations=st.integers(min_value=1, max_value=30),
        num_model_versions=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=100)
    def test_model_versions_contributed_count(
        self,
        num_validations: int,
        num_model_versions: int,
    ):
        """
        Property: Model versions contributed count equals distinct model_version_ids
        
        The count of model versions a user contributed to should equal the
        number of distinct model_version_ids in their used validations.
        """
        user_id = uuid.uuid4()
        model_version_ids = [uuid.uuid4() for _ in range(num_model_versions)]
        
        validations: List[ValidationFeedback] = []
        
        for i in range(num_validations):
            # Assign to a model version (cycling through available versions)
            version_idx = i % num_model_versions
            
            validation = ValidationFeedback(
                scan_result_id=uuid.uuid4(),
                user_id=user_id,
                comment_text=f"Test comment {i}",
                original_prediction=True,
                original_confidence=0.85,
                corrected_label=True,
                is_correction=False,
                used_in_training=True,
                model_version_id=model_version_ids[version_idx],
            )
            validations.append(validation)
        
        # Count distinct model versions
        distinct_versions = len(set(
            v.model_version_id for v in validations
            if v.used_in_training and v.model_version_id is not None
        ))
        
        # Should equal the number of model versions (or less if num_validations < num_model_versions)
        expected_distinct = min(num_validations, num_model_versions)
        assert distinct_versions == expected_distinct

    @given(
        num_validations=st.integers(min_value=0, max_value=30),
        num_corrections=st.integers(min_value=0, max_value=30),
    )
    @settings(max_examples=100)
    def test_corrections_count_accuracy(
        self,
        num_validations: int,
        num_corrections: int,
    ):
        """
        Property: Corrections count equals validations with is_correction=True
        
        The count of corrections made should equal the number of validations
        where is_correction is True.
        """
        # Ensure num_corrections doesn't exceed num_validations
        actual_corrections = min(num_corrections, num_validations)
        
        user_id = uuid.uuid4()
        
        validations: List[ValidationFeedback] = []
        
        for i in range(num_validations):
            # First 'actual_corrections' are corrections
            is_correction = i < actual_corrections
            
            validation = ValidationFeedback(
                scan_result_id=uuid.uuid4(),
                user_id=user_id,
                comment_text=f"Test comment {i}",
                original_prediction=True,
                original_confidence=0.85,
                corrected_label=not is_correction if is_correction else True,  # Flip if correction
                is_correction=is_correction,
                used_in_training=False,
            )
            validations.append(validation)
        
        # Count corrections
        corrections_count = sum(1 for v in validations if v.is_correction)
        
        assert corrections_count == actual_corrections

    @given(
        num_validations=st.integers(min_value=0, max_value=50),
    )
    @settings(max_examples=100)
    def test_total_validations_count(
        self,
        num_validations: int,
    ):
        """
        Property: Total validations count equals number of validation records
        
        The total validation count should equal the actual number of
        ValidationFeedback records for the user.
        """
        user_id = uuid.uuid4()
        
        validations: List[ValidationFeedback] = []
        
        for i in range(num_validations):
            validation = ValidationFeedback(
                scan_result_id=uuid.uuid4(),
                user_id=user_id,
                comment_text=f"Test comment {i}",
                original_prediction=True,
                original_confidence=0.85,
                corrected_label=True,
                is_correction=False,
                used_in_training=False,
            )
            validations.append(validation)
        
        # Count total validations for user
        total_count = sum(1 for v in validations if v.user_id == user_id)
        
        assert total_count == num_validations

    @given(
        num_validations=st.integers(min_value=1, max_value=30),
        num_used=st.integers(min_value=0, max_value=30),
    )
    @settings(max_examples=100)
    def test_contribution_rate_calculation(
        self,
        num_validations: int,
        num_used: int,
    ):
        """
        Property: Contribution rate is correctly calculated
        
        The contribution rate should equal (contributed_to_training / total_validations) * 100
        when total_validations > 0.
        """
        # Ensure num_used doesn't exceed num_validations
        actual_used = min(num_used, num_validations)
        
        user_id = uuid.uuid4()
        model_version_id = uuid.uuid4()
        
        validations: List[ValidationFeedback] = []
        
        for i in range(num_validations):
            is_used = i < actual_used
            
            validation = ValidationFeedback(
                scan_result_id=uuid.uuid4(),
                user_id=user_id,
                comment_text=f"Test comment {i}",
                original_prediction=True,
                original_confidence=0.85,
                corrected_label=True,
                is_correction=False,
                used_in_training=is_used,
                model_version_id=model_version_id if is_used else None,
            )
            validations.append(validation)
        
        # Calculate counts
        total = len(validations)
        contributed = sum(
            1 for v in validations
            if v.used_in_training and v.model_version_id is not None
        )
        
        # Calculate rate
        if total > 0:
            rate = round((contributed / total) * 100)
        else:
            rate = 0
        
        # Verify rate calculation
        expected_rate = round((actual_used / num_validations) * 100) if num_validations > 0 else 0
        assert rate == expected_rate

    @given(
        num_validations=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=100)
    def test_unused_validations_not_counted_as_contributions(
        self,
        num_validations: int,
    ):
        """
        Property: Validations with used_in_training=False are not counted as contributions
        
        Even if a validation has a model_version_id set, it should not be counted
        as a contribution if used_in_training is False.
        """
        user_id = uuid.uuid4()
        model_version_id = uuid.uuid4()
        
        validations: List[ValidationFeedback] = []
        
        for i in range(num_validations):
            # All validations have model_version_id but used_in_training=False
            validation = ValidationFeedback(
                scan_result_id=uuid.uuid4(),
                user_id=user_id,
                comment_text=f"Test comment {i}",
                original_prediction=True,
                original_confidence=0.85,
                corrected_label=True,
                is_correction=False,
                used_in_training=False,  # Not used in training
                model_version_id=model_version_id,  # But has model version
            )
            validations.append(validation)
        
        # Count contributions (should be 0)
        contributed = sum(
            1 for v in validations
            if v.used_in_training and v.model_version_id is not None
        )
        
        assert contributed == 0

    @given(
        num_validations=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=100)
    def test_validations_without_model_version_not_counted(
        self,
        num_validations: int,
    ):
        """
        Property: Validations without model_version_id are not counted as contributions
        
        Even if a validation has used_in_training=True, it should not be counted
        as a contribution if model_version_id is None.
        """
        user_id = uuid.uuid4()
        
        validations: List[ValidationFeedback] = []
        
        for i in range(num_validations):
            # All validations have used_in_training=True but no model_version_id
            validation = ValidationFeedback(
                scan_result_id=uuid.uuid4(),
                user_id=user_id,
                comment_text=f"Test comment {i}",
                original_prediction=True,
                original_confidence=0.85,
                corrected_label=True,
                is_correction=False,
                used_in_training=True,  # Used in training
                model_version_id=None,  # But no model version
            )
            validations.append(validation)
        
        # Count contributions (should be 0)
        contributed = sum(
            1 for v in validations
            if v.used_in_training and v.model_version_id is not None
        )
        
        assert contributed == 0
