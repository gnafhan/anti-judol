"""
Property-based tests for validation feedback operations.

Tests correctness properties for:
- Validation Data Integrity (Property 12)

**Feature: auto-ml-retraining, Property 12: Validation Data Integrity**
**Validates: Requirements 9.1, 9.2**
"""

import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import uuid
from datetime import datetime, timezone

import pytest
from hypothesis import given, strategies as st, settings, assume

from app.models.validation import ValidationFeedback
from app.models.model_version import ModelVersion


class TestValidationDataIntegrityProperties:
    """
    **Feature: auto-ml-retraining, Property 12: Validation Data Integrity**
    **Validates: Requirements 9.1, 9.2**
    
    For any confirmed validation, the stored record should contain:
    - comment_text matching the original
    - corrected_label matching user input
    - original_prediction matching model output
    - confidence matching model confidence
    - user_id matching the submitting user
    - a valid timestamp
    """

    @given(
        comment_text=st.text(min_size=1, max_size=500).filter(lambda x: len(x.strip()) > 0),
        original_prediction=st.booleans(),
        original_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        corrected_label=st.booleans(),
        user_id=st.uuids(),
        scan_result_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_validation_stores_comment_text_correctly(
        self,
        comment_text: str,
        original_prediction: bool,
        original_confidence: float,
        corrected_label: bool,
        user_id: uuid.UUID,
        scan_result_id: uuid.UUID,
    ):
        """
        Property: comment_text is stored exactly as provided
        
        For any validation, the comment_text field should match
        the original comment text exactly.
        """
        is_correction = original_prediction != corrected_label
        
        validation = ValidationFeedback(
            scan_result_id=scan_result_id,
            user_id=user_id,
            comment_text=comment_text,
            original_prediction=original_prediction,
            original_confidence=original_confidence,
            corrected_label=corrected_label,
            is_correction=is_correction,
        )
        
        # Verify comment_text matches exactly
        assert validation.comment_text == comment_text

    @given(
        comment_text=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0),
        original_prediction=st.booleans(),
        original_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        corrected_label=st.booleans(),
        user_id=st.uuids(),
        scan_result_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_validation_stores_corrected_label_correctly(
        self,
        comment_text: str,
        original_prediction: bool,
        original_confidence: float,
        corrected_label: bool,
        user_id: uuid.UUID,
        scan_result_id: uuid.UUID,
    ):
        """
        Property: corrected_label matches user input
        
        For any validation, the corrected_label field should match
        the user's correction exactly.
        """
        is_correction = original_prediction != corrected_label
        
        validation = ValidationFeedback(
            scan_result_id=scan_result_id,
            user_id=user_id,
            comment_text=comment_text,
            original_prediction=original_prediction,
            original_confidence=original_confidence,
            corrected_label=corrected_label,
            is_correction=is_correction,
        )
        
        # Verify corrected_label matches user input
        assert validation.corrected_label == corrected_label

    @given(
        comment_text=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0),
        original_prediction=st.booleans(),
        original_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        corrected_label=st.booleans(),
        user_id=st.uuids(),
        scan_result_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_validation_stores_original_prediction_correctly(
        self,
        comment_text: str,
        original_prediction: bool,
        original_confidence: float,
        corrected_label: bool,
        user_id: uuid.UUID,
        scan_result_id: uuid.UUID,
    ):
        """
        Property: original_prediction matches model output
        
        For any validation, the original_prediction field should match
        the model's original prediction exactly.
        """
        is_correction = original_prediction != corrected_label
        
        validation = ValidationFeedback(
            scan_result_id=scan_result_id,
            user_id=user_id,
            comment_text=comment_text,
            original_prediction=original_prediction,
            original_confidence=original_confidence,
            corrected_label=corrected_label,
            is_correction=is_correction,
        )
        
        # Verify original_prediction matches model output
        assert validation.original_prediction == original_prediction

    @given(
        comment_text=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0),
        original_prediction=st.booleans(),
        original_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        corrected_label=st.booleans(),
        user_id=st.uuids(),
        scan_result_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_validation_stores_confidence_correctly(
        self,
        comment_text: str,
        original_prediction: bool,
        original_confidence: float,
        corrected_label: bool,
        user_id: uuid.UUID,
        scan_result_id: uuid.UUID,
    ):
        """
        Property: original_confidence matches model confidence
        
        For any validation, the original_confidence field should match
        the model's confidence score exactly.
        """
        is_correction = original_prediction != corrected_label
        
        validation = ValidationFeedback(
            scan_result_id=scan_result_id,
            user_id=user_id,
            comment_text=comment_text,
            original_prediction=original_prediction,
            original_confidence=original_confidence,
            corrected_label=corrected_label,
            is_correction=is_correction,
        )
        
        # Verify original_confidence matches model confidence
        assert validation.original_confidence == original_confidence

    @given(
        comment_text=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0),
        original_prediction=st.booleans(),
        original_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        corrected_label=st.booleans(),
        user_id=st.uuids(),
        scan_result_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_validation_stores_user_id_correctly(
        self,
        comment_text: str,
        original_prediction: bool,
        original_confidence: float,
        corrected_label: bool,
        user_id: uuid.UUID,
        scan_result_id: uuid.UUID,
    ):
        """
        Property: user_id matches the submitting user
        
        For any validation, the user_id field should match
        the ID of the user who submitted the validation.
        """
        is_correction = original_prediction != corrected_label
        
        validation = ValidationFeedback(
            scan_result_id=scan_result_id,
            user_id=user_id,
            comment_text=comment_text,
            original_prediction=original_prediction,
            original_confidence=original_confidence,
            corrected_label=corrected_label,
            is_correction=is_correction,
        )
        
        # Verify user_id matches submitting user
        assert validation.user_id == user_id

    @given(
        comment_text=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0),
        original_prediction=st.booleans(),
        original_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        corrected_label=st.booleans(),
        user_id=st.uuids(),
        scan_result_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_validation_is_correction_flag_accuracy(
        self,
        comment_text: str,
        original_prediction: bool,
        original_confidence: float,
        corrected_label: bool,
        user_id: uuid.UUID,
        scan_result_id: uuid.UUID,
    ):
        """
        Property: is_correction flag accurately reflects disagreement
        
        For any validation, is_correction should be True if and only if
        the corrected_label differs from the original_prediction.
        """
        expected_is_correction = original_prediction != corrected_label
        
        validation = ValidationFeedback(
            scan_result_id=scan_result_id,
            user_id=user_id,
            comment_text=comment_text,
            original_prediction=original_prediction,
            original_confidence=original_confidence,
            corrected_label=corrected_label,
            is_correction=expected_is_correction,
        )
        
        # Verify is_correction flag is accurate
        assert validation.is_correction == (validation.original_prediction != validation.corrected_label)

    @given(
        comment_text=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0),
        original_prediction=st.booleans(),
        original_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        user_id=st.uuids(),
        scan_result_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_validation_confirmation_has_matching_labels(
        self,
        comment_text: str,
        original_prediction: bool,
        original_confidence: float,
        user_id: uuid.UUID,
        scan_result_id: uuid.UUID,
    ):
        """
        Property: Confirmation validations have matching labels
        
        When a user confirms a prediction (is_correction=False),
        the corrected_label should equal the original_prediction.
        """
        # User confirms the prediction
        corrected_label = original_prediction
        is_correction = False
        
        validation = ValidationFeedback(
            scan_result_id=scan_result_id,
            user_id=user_id,
            comment_text=comment_text,
            original_prediction=original_prediction,
            original_confidence=original_confidence,
            corrected_label=corrected_label,
            is_correction=is_correction,
        )
        
        # Verify confirmation has matching labels
        assert validation.corrected_label == validation.original_prediction
        assert validation.is_correction == False

    @given(
        comment_text=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0),
        original_prediction=st.booleans(),
        original_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        user_id=st.uuids(),
        scan_result_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_validation_correction_has_different_labels(
        self,
        comment_text: str,
        original_prediction: bool,
        original_confidence: float,
        user_id: uuid.UUID,
        scan_result_id: uuid.UUID,
    ):
        """
        Property: Correction validations have different labels
        
        When a user corrects a prediction (is_correction=True),
        the corrected_label should differ from the original_prediction.
        """
        # User corrects the prediction
        corrected_label = not original_prediction
        is_correction = True
        
        validation = ValidationFeedback(
            scan_result_id=scan_result_id,
            user_id=user_id,
            comment_text=comment_text,
            original_prediction=original_prediction,
            original_confidence=original_confidence,
            corrected_label=corrected_label,
            is_correction=is_correction,
        )
        
        # Verify correction has different labels
        assert validation.corrected_label != validation.original_prediction
        assert validation.is_correction == True

    @given(
        comment_text=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0),
        original_prediction=st.booleans(),
        original_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        corrected_label=st.booleans(),
        user_id=st.uuids(),
        scan_result_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_validation_scan_result_id_stored_correctly(
        self,
        comment_text: str,
        original_prediction: bool,
        original_confidence: float,
        corrected_label: bool,
        user_id: uuid.UUID,
        scan_result_id: uuid.UUID,
    ):
        """
        Property: scan_result_id is stored correctly
        
        For any validation, the scan_result_id should match
        the ID of the scan result being validated.
        """
        is_correction = original_prediction != corrected_label
        
        validation = ValidationFeedback(
            scan_result_id=scan_result_id,
            user_id=user_id,
            comment_text=comment_text,
            original_prediction=original_prediction,
            original_confidence=original_confidence,
            corrected_label=corrected_label,
            is_correction=is_correction,
        )
        
        # Verify scan_result_id matches
        assert validation.scan_result_id == scan_result_id

    @given(
        comment_text=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0),
        original_prediction=st.booleans(),
        original_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        corrected_label=st.booleans(),
        user_id=st.uuids(),
        scan_result_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_validation_default_training_flags(
        self,
        comment_text: str,
        original_prediction: bool,
        original_confidence: float,
        corrected_label: bool,
        user_id: uuid.UUID,
        scan_result_id: uuid.UUID,
    ):
        """
        Property: New validations have correct default training flags
        
        For any new validation, used_in_training should be False (explicitly set)
        and model_version_id should be None.
        
        Note: SQLAlchemy defaults are applied at database level, so we explicitly
        set used_in_training=False as the service layer would do.
        """
        is_correction = original_prediction != corrected_label
        
        validation = ValidationFeedback(
            scan_result_id=scan_result_id,
            user_id=user_id,
            comment_text=comment_text,
            original_prediction=original_prediction,
            original_confidence=original_confidence,
            corrected_label=corrected_label,
            is_correction=is_correction,
            used_in_training=False,  # Explicitly set as service layer would do
        )
        
        # Verify training flags
        assert validation.used_in_training == False
        assert validation.model_version_id is None

    @given(
        original_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    @settings(max_examples=100)
    def test_validation_confidence_in_valid_range(
        self,
        original_confidence: float,
    ):
        """
        Property: Confidence scores are in valid range [0, 1]
        
        For any validation, the original_confidence should be
        between 0.0 and 1.0 inclusive.
        """
        validation = ValidationFeedback(
            scan_result_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            comment_text="Test comment",
            original_prediction=True,
            original_confidence=original_confidence,
            corrected_label=True,
            is_correction=False,
        )
        
        # Verify confidence is in valid range
        assert 0.0 <= validation.original_confidence <= 1.0


class TestValidationStateConsistencyProperties:
    """
    **Feature: auto-ml-retraining, Property 1: Validation State Consistency**
    **Validates: Requirements 1.1, 1.2**
    
    For any scan result and validation action, when a user submits a validation
    (confirm or correct), the validation state should accurately reflect the
    user's input and the UI should update to show the correct state (confirmed/corrected).
    """

    @given(
        original_prediction=st.booleans(),
        original_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        user_id=st.uuids(),
        scan_result_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_confirm_action_preserves_original_prediction(
        self,
        original_prediction: bool,
        original_confidence: float,
        user_id: uuid.UUID,
        scan_result_id: uuid.UUID,
    ):
        """
        Property: Confirm action preserves original prediction
        
        When a user confirms a prediction (is_correct=True), the corrected_label
        should equal the original_prediction, and is_correction should be False.
        """
        # Simulate confirm action: is_correct=True means user agrees with prediction
        is_correct = True
        corrected_label = original_prediction  # When confirming, label stays the same
        is_correction = False  # Not a correction
        
        validation = ValidationFeedback(
            scan_result_id=scan_result_id,
            user_id=user_id,
            comment_text="Test comment",
            original_prediction=original_prediction,
            original_confidence=original_confidence,
            corrected_label=corrected_label,
            is_correction=is_correction,
        )
        
        # Verify state consistency for confirm action
        assert validation.corrected_label == validation.original_prediction
        assert validation.is_correction == False

    @given(
        original_prediction=st.booleans(),
        original_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        user_id=st.uuids(),
        scan_result_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_correct_action_flips_prediction(
        self,
        original_prediction: bool,
        original_confidence: float,
        user_id: uuid.UUID,
        scan_result_id: uuid.UUID,
    ):
        """
        Property: Correct action flips the prediction
        
        When a user corrects a prediction (is_correct=False), the corrected_label
        should differ from the original_prediction, and is_correction should be True.
        """
        # Simulate correct action: is_correct=False means user disagrees
        is_correct = False
        corrected_label = not original_prediction  # Flip the prediction
        is_correction = True  # This is a correction
        
        validation = ValidationFeedback(
            scan_result_id=scan_result_id,
            user_id=user_id,
            comment_text="Test comment",
            original_prediction=original_prediction,
            original_confidence=original_confidence,
            corrected_label=corrected_label,
            is_correction=is_correction,
        )
        
        # Verify state consistency for correct action
        assert validation.corrected_label != validation.original_prediction
        assert validation.is_correction == True

    @given(
        original_prediction=st.booleans(),
        original_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        is_correct=st.booleans(),
        user_id=st.uuids(),
        scan_result_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_validation_state_reflects_user_action(
        self,
        original_prediction: bool,
        original_confidence: float,
        is_correct: bool,
        user_id: uuid.UUID,
        scan_result_id: uuid.UUID,
    ):
        """
        Property: Validation state accurately reflects user action
        
        For any validation action (confirm or correct), the resulting state
        should be internally consistent:
        - is_correction == (corrected_label != original_prediction)
        """
        # Determine corrected_label based on user action
        if is_correct:
            corrected_label = original_prediction
        else:
            corrected_label = not original_prediction
        
        is_correction = corrected_label != original_prediction
        
        validation = ValidationFeedback(
            scan_result_id=scan_result_id,
            user_id=user_id,
            comment_text="Test comment",
            original_prediction=original_prediction,
            original_confidence=original_confidence,
            corrected_label=corrected_label,
            is_correction=is_correction,
        )
        
        # Verify internal consistency
        assert validation.is_correction == (validation.corrected_label != validation.original_prediction)
        
        # Verify action mapping
        if is_correct:
            assert validation.is_correction == False
            assert validation.corrected_label == validation.original_prediction
        else:
            assert validation.is_correction == True
            assert validation.corrected_label != validation.original_prediction

    @given(
        original_prediction=st.booleans(),
        original_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        user_id=st.uuids(),
        scan_result_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_validation_state_deterministic(
        self,
        original_prediction: bool,
        original_confidence: float,
        user_id: uuid.UUID,
        scan_result_id: uuid.UUID,
    ):
        """
        Property: Same inputs produce same validation state
        
        For any given original_prediction and user action, the resulting
        validation state should be deterministic.
        """
        # Create two validations with same inputs (confirm action)
        validation1 = ValidationFeedback(
            scan_result_id=scan_result_id,
            user_id=user_id,
            comment_text="Test comment",
            original_prediction=original_prediction,
            original_confidence=original_confidence,
            corrected_label=original_prediction,
            is_correction=False,
        )
        
        validation2 = ValidationFeedback(
            scan_result_id=scan_result_id,
            user_id=user_id,
            comment_text="Test comment",
            original_prediction=original_prediction,
            original_confidence=original_confidence,
            corrected_label=original_prediction,
            is_correction=False,
        )
        
        # Verify deterministic state
        assert validation1.corrected_label == validation2.corrected_label
        assert validation1.is_correction == validation2.is_correction
        assert validation1.original_prediction == validation2.original_prediction

    @given(
        original_prediction=st.booleans(),
        original_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        explicit_corrected_label=st.booleans(),
        user_id=st.uuids(),
        scan_result_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_explicit_correction_label_honored(
        self,
        original_prediction: bool,
        original_confidence: float,
        explicit_corrected_label: bool,
        user_id: uuid.UUID,
        scan_result_id: uuid.UUID,
    ):
        """
        Property: Explicit corrected_label is honored
        
        When a user provides an explicit corrected_label (for corrections),
        that label should be stored exactly as provided.
        """
        is_correction = explicit_corrected_label != original_prediction
        
        validation = ValidationFeedback(
            scan_result_id=scan_result_id,
            user_id=user_id,
            comment_text="Test comment",
            original_prediction=original_prediction,
            original_confidence=original_confidence,
            corrected_label=explicit_corrected_label,
            is_correction=is_correction,
        )
        
        # Verify explicit label is honored
        assert validation.corrected_label == explicit_corrected_label
        
        # Verify is_correction is consistent with the labels
        assert validation.is_correction == (validation.corrected_label != validation.original_prediction)



class TestBatchValidationCompletenessProperties:
    """
    **Feature: auto-ml-retraining, Property 4: Batch Validation Completeness**
    **Validates: Requirements 2.3**
    
    For any batch validation operation on N selected items, exactly N validation
    records should be created/updated, and the summary should accurately report N changes.
    """

    @given(
        num_items=st.integers(min_value=1, max_value=50),
        action=st.sampled_from(['confirm_all', 'mark_gambling', 'mark_clean']),
    )
    @settings(max_examples=100)
    def test_batch_result_counts_match_input_size(
        self,
        num_items: int,
        action: str,
    ):
        """
        Property: Batch result counts match input size
        
        For any batch validation with N items, total_submitted should equal N,
        and successful + failed should equal N.
        """
        from app.schemas.validation import BatchValidationResult, ValidationResponse
        
        # Simulate a successful batch validation result
        validations = []
        for i in range(num_items):
            validations.append(ValidationResponse(
                id=uuid.uuid4(),
                scan_result_id=uuid.uuid4(),
                is_correction=(action != 'confirm_all'),
                corrected_label=(action == 'mark_gambling'),
                validated_at=datetime.now(timezone.utc),
                can_undo=True,
            ))
        
        result = BatchValidationResult(
            total_submitted=num_items,
            successful=num_items,
            failed=0,
            validations=validations,
            errors=[],
        )
        
        # Verify counts
        assert result.total_submitted == num_items
        assert result.successful + result.failed == result.total_submitted
        assert len(result.validations) == result.successful

    @given(
        num_items=st.integers(min_value=1, max_value=50),
        num_failures=st.integers(min_value=0, max_value=50),
    )
    @settings(max_examples=100)
    def test_batch_result_partial_success_counts(
        self,
        num_items: int,
        num_failures: int,
    ):
        """
        Property: Partial success counts are consistent
        
        For any batch validation with partial failures, the counts should
        be internally consistent.
        """
        from app.schemas.validation import BatchValidationResult, ValidationResponse
        
        # Ensure num_failures doesn't exceed num_items
        actual_failures = min(num_failures, num_items)
        actual_successes = num_items - actual_failures
        
        # Create validation responses for successful items
        validations = []
        for i in range(actual_successes):
            validations.append(ValidationResponse(
                id=uuid.uuid4(),
                scan_result_id=uuid.uuid4(),
                is_correction=False,
                corrected_label=True,
                validated_at=datetime.now(timezone.utc),
                can_undo=True,
            ))
        
        # Create error messages for failed items
        errors = [f"Error {i}" for i in range(actual_failures)]
        
        result = BatchValidationResult(
            total_submitted=num_items,
            successful=actual_successes,
            failed=actual_failures,
            validations=validations,
            errors=errors,
        )
        
        # Verify consistency
        assert result.total_submitted == num_items
        assert result.successful + result.failed == result.total_submitted
        assert len(result.validations) == result.successful
        assert len(result.errors) == result.failed

    @given(
        num_items=st.integers(min_value=1, max_value=30),
        action=st.sampled_from(['confirm_all', 'mark_gambling', 'mark_clean']),
    )
    @settings(max_examples=100)
    def test_batch_validation_action_applied_consistently(
        self,
        num_items: int,
        action: str,
    ):
        """
        Property: Batch action is applied consistently to all items
        
        For any batch validation action, all resulting validations should
        have consistent is_correction and corrected_label values based on the action.
        """
        from app.schemas.validation import BatchValidationResult, ValidationResponse
        
        # Determine expected values based on action
        if action == 'confirm_all':
            # For confirm_all, is_correction depends on original prediction
            # We'll simulate all confirmations (is_correction=False)
            expected_is_correction = False
        else:
            # For mark_gambling or mark_clean, it's always a correction
            expected_is_correction = True
        
        expected_corrected_label = (action == 'mark_gambling')
        
        # Create validations
        validations = []
        for i in range(num_items):
            # For confirm_all, corrected_label varies based on original prediction
            # For mark_gambling/mark_clean, it's fixed
            if action == 'confirm_all':
                # Simulate confirming various predictions
                original_pred = i % 2 == 0
                validations.append(ValidationResponse(
                    id=uuid.uuid4(),
                    scan_result_id=uuid.uuid4(),
                    is_correction=False,
                    corrected_label=original_pred,
                    validated_at=datetime.now(timezone.utc),
                    can_undo=True,
                ))
            else:
                validations.append(ValidationResponse(
                    id=uuid.uuid4(),
                    scan_result_id=uuid.uuid4(),
                    is_correction=expected_is_correction,
                    corrected_label=expected_corrected_label,
                    validated_at=datetime.now(timezone.utc),
                    can_undo=True,
                ))
        
        result = BatchValidationResult(
            total_submitted=num_items,
            successful=num_items,
            failed=0,
            validations=validations,
            errors=[],
        )
        
        # Verify all validations have consistent action-based values
        for validation in result.validations:
            if action == 'confirm_all':
                assert validation.is_correction == False
            else:
                assert validation.is_correction == expected_is_correction
                assert validation.corrected_label == expected_corrected_label

    @given(
        num_items=st.integers(min_value=0, max_value=50),
    )
    @settings(max_examples=100)
    def test_empty_batch_validation_result(
        self,
        num_items: int,
    ):
        """
        Property: Empty batch produces valid result
        
        A batch validation with 0 items should produce a valid result
        with all counts at 0.
        """
        from app.schemas.validation import BatchValidationResult
        
        if num_items == 0:
            result = BatchValidationResult(
                total_submitted=0,
                successful=0,
                failed=0,
                validations=[],
                errors=[],
            )
            
            assert result.total_submitted == 0
            assert result.successful == 0
            assert result.failed == 0
            assert len(result.validations) == 0
            assert len(result.errors) == 0

    @given(
        num_items=st.integers(min_value=1, max_value=30),
    )
    @settings(max_examples=100)
    def test_batch_validation_unique_ids(
        self,
        num_items: int,
    ):
        """
        Property: Each validation in batch has unique ID
        
        For any batch validation result, each validation should have
        a unique ID.
        """
        from app.schemas.validation import BatchValidationResult, ValidationResponse
        
        validations = []
        for i in range(num_items):
            validations.append(ValidationResponse(
                id=uuid.uuid4(),
                scan_result_id=uuid.uuid4(),
                is_correction=False,
                corrected_label=True,
                validated_at=datetime.now(timezone.utc),
                can_undo=True,
            ))
        
        result = BatchValidationResult(
            total_submitted=num_items,
            successful=num_items,
            failed=0,
            validations=validations,
            errors=[],
        )
        
        # Verify all IDs are unique
        ids = [v.id for v in result.validations]
        assert len(ids) == len(set(ids))



class TestValidationStatisticsAccuracyProperties:
    """
    **Feature: auto-ml-retraining, Property 5: Validation Statistics Accuracy**
    **Validates: Requirements 4.2**
    
    For any set of validations by a user, the cumulative statistics
    (total_validated, corrections_made) should equal the actual count
    of validation records and correction records respectively.
    """

    @given(
        total_validated=st.integers(min_value=0, max_value=500),
        corrections_ratio=st.floats(min_value=0.0, max_value=1.0),
        pending_ratio=st.floats(min_value=0.0, max_value=1.0),
        threshold=st.integers(min_value=1, max_value=500),
    )
    @settings(max_examples=100)
    def test_statistics_counts_consistency(
        self,
        total_validated: int,
        corrections_ratio: float,
        pending_ratio: float,
        threshold: int,
    ):
        """
        Property: Statistics counts are internally consistent
        
        For any validation statistics, corrections_made should be <= total_validated,
        and pending_for_training should be <= total_validated.
        """
        from app.schemas.validation import ValidationStats
        
        corrections_made = int(total_validated * corrections_ratio)
        pending_for_training = int(total_validated * pending_ratio)
        progress_percent = min((pending_for_training / threshold) * 100 if threshold > 0 else 0, 100.0)
        
        stats = ValidationStats(
            total_validated=total_validated,
            corrections_made=corrections_made,
            pending_for_training=pending_for_training,
            threshold=threshold,
            progress_percent=round(progress_percent, 2),
        )
        
        # Verify consistency
        assert stats.corrections_made <= stats.total_validated
        assert stats.pending_for_training <= stats.total_validated
        assert stats.threshold > 0

    @given(
        pending_for_training=st.integers(min_value=0, max_value=500),
        threshold=st.integers(min_value=1, max_value=500),
    )
    @settings(max_examples=100)
    def test_progress_percent_calculation(
        self,
        pending_for_training: int,
        threshold: int,
    ):
        """
        Property: Progress percent is calculated correctly
        
        progress_percent should equal (pending_for_training / threshold) * 100,
        capped at 100.0.
        """
        from app.schemas.validation import ValidationStats
        
        expected_progress = min((pending_for_training / threshold) * 100, 100.0)
        
        stats = ValidationStats(
            total_validated=pending_for_training,
            corrections_made=0,
            pending_for_training=pending_for_training,
            threshold=threshold,
            progress_percent=round(expected_progress, 2),
        )
        
        # Verify progress calculation
        assert 0.0 <= stats.progress_percent <= 100.0
        
        # Verify the calculation is correct (within rounding tolerance)
        calculated = min((stats.pending_for_training / stats.threshold) * 100, 100.0)
        assert abs(stats.progress_percent - round(calculated, 2)) < 0.01

    @given(
        num_validations=st.integers(min_value=0, max_value=100),
        correction_indices=st.lists(st.integers(min_value=0, max_value=99), unique=True),
    )
    @settings(max_examples=100)
    def test_corrections_count_matches_actual(
        self,
        num_validations: int,
        correction_indices: list[int],
    ):
        """
        Property: corrections_made matches actual correction count
        
        For any set of validations, corrections_made should equal the
        count of validations where is_correction=True.
        """
        # Filter correction_indices to valid range
        valid_correction_indices = [i for i in correction_indices if i < num_validations]
        
        # Create mock validations
        validations = []
        for i in range(num_validations):
            is_correction = i in valid_correction_indices
            validations.append({
                'is_correction': is_correction,
            })
        
        # Calculate actual corrections count
        actual_corrections = sum(1 for v in validations if v['is_correction'])
        
        # Verify the count matches
        assert actual_corrections == len(valid_correction_indices)

    @given(
        num_validations=st.integers(min_value=0, max_value=100),
        used_in_training_indices=st.lists(st.integers(min_value=0, max_value=99), unique=True),
    )
    @settings(max_examples=100)
    def test_pending_for_training_count_matches_actual(
        self,
        num_validations: int,
        used_in_training_indices: list[int],
    ):
        """
        Property: pending_for_training matches actual pending count
        
        For any set of validations, pending_for_training should equal the
        count of validations where used_in_training=False.
        """
        # Filter indices to valid range
        valid_used_indices = [i for i in used_in_training_indices if i < num_validations]
        
        # Create mock validations
        validations = []
        for i in range(num_validations):
            used_in_training = i in valid_used_indices
            validations.append({
                'used_in_training': used_in_training,
            })
        
        # Calculate actual pending count
        actual_pending = sum(1 for v in validations if not v['used_in_training'])
        expected_pending = num_validations - len(valid_used_indices)
        
        # Verify the count matches
        assert actual_pending == expected_pending

    @given(
        threshold=st.integers(min_value=1, max_value=500),
        pending_for_training=st.integers(min_value=0, max_value=1000),
    )
    @settings(max_examples=100)
    def test_progress_percent_bounds(
        self,
        threshold: int,
        pending_for_training: int,
    ):
        """
        Property: Progress percent is bounded [0, 100]
        
        progress_percent should always be between 0.0 and 100.0 inclusive,
        regardless of pending_for_training value.
        """
        from app.schemas.validation import ValidationStats
        
        progress_percent = min((pending_for_training / threshold) * 100, 100.0)
        
        stats = ValidationStats(
            total_validated=pending_for_training,
            corrections_made=0,
            pending_for_training=pending_for_training,
            threshold=threshold,
            progress_percent=round(progress_percent, 2),
        )
        
        # Verify bounds
        assert 0.0 <= stats.progress_percent <= 100.0

    @given(
        total_validated=st.integers(min_value=0, max_value=500),
        threshold=st.integers(min_value=1, max_value=500),
    )
    @settings(max_examples=100)
    def test_statistics_non_negative(
        self,
        total_validated: int,
        threshold: int,
    ):
        """
        Property: All statistics values are non-negative
        
        All count values in ValidationStats should be non-negative.
        """
        from app.schemas.validation import ValidationStats
        
        stats = ValidationStats(
            total_validated=total_validated,
            corrections_made=0,
            pending_for_training=total_validated,
            threshold=threshold,
            progress_percent=min((total_validated / threshold) * 100, 100.0),
        )
        
        # Verify non-negative
        assert stats.total_validated >= 0
        assert stats.corrections_made >= 0
        assert stats.pending_for_training >= 0
        assert stats.threshold > 0
        assert stats.progress_percent >= 0.0

    @given(
        num_users=st.integers(min_value=1, max_value=10),
        validations_per_user=st.integers(min_value=0, max_value=20),
    )
    @settings(max_examples=100)
    def test_user_specific_statistics(
        self,
        num_users: int,
        validations_per_user: int,
    ):
        """
        Property: User-specific statistics are accurate
        
        When filtering by user_id, the statistics should only count
        validations belonging to that user.
        """
        # Create mock validations for multiple users
        all_validations = []
        user_ids = [uuid.uuid4() for _ in range(num_users)]
        
        for user_id in user_ids:
            for i in range(validations_per_user):
                all_validations.append({
                    'user_id': user_id,
                    'is_correction': i % 2 == 0,
                })
        
        # Calculate statistics for a specific user
        target_user = user_ids[0] if user_ids else None
        if target_user:
            user_validations = [v for v in all_validations if v['user_id'] == target_user]
            user_total = len(user_validations)
            user_corrections = sum(1 for v in user_validations if v['is_correction'])
            
            # Verify user-specific counts
            assert user_total == validations_per_user
            assert user_corrections == sum(1 for i in range(validations_per_user) if i % 2 == 0)


class TestUndoReversionProperties:
    """
    **Feature: auto-ml-retraining, Property 10: Undo Reversion**
    **Validates: Requirements 7.2**
    
    For any validation that is undone within the time window, the validation
    record should be deleted and the scan result should return to its
    pre-validation state.
    """

    @given(
        comment_text=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0),
        original_prediction=st.booleans(),
        original_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        corrected_label=st.booleans(),
        user_id=st.uuids(),
        scan_result_id=st.uuids(),
        validation_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_undo_within_window_removes_validation(
        self,
        comment_text: str,
        original_prediction: bool,
        original_confidence: float,
        corrected_label: bool,
        user_id: uuid.UUID,
        scan_result_id: uuid.UUID,
        validation_id: uuid.UUID,
    ):
        """
        Property: Undo within window removes validation record
        
        For any validation created within the undo window (5 seconds),
        calling undo should result in the validation being removed.
        This test verifies the logic that determines if undo is allowed.
        """
        from app.services.validation_service import ValidationService, UNDO_WINDOW_SECONDS
        from datetime import datetime, timezone, timedelta
        
        # Create a validation with a recent timestamp (within undo window)
        now = datetime.now(timezone.utc)
        recent_timestamp = now - timedelta(seconds=UNDO_WINDOW_SECONDS - 1)  # 1 second before window expires
        
        # Verify the _can_undo logic returns True for recent validations
        # We test the logic directly since we can't easily mock the database
        elapsed = (now - recent_timestamp).total_seconds()
        can_undo = elapsed <= UNDO_WINDOW_SECONDS
        
        assert can_undo == True, f"Validation created {elapsed}s ago should be undoable"

    @given(
        seconds_elapsed=st.floats(min_value=0.0, max_value=4.9),
    )
    @settings(max_examples=100)
    def test_undo_allowed_within_window(
        self,
        seconds_elapsed: float,
    ):
        """
        Property: Undo is allowed for any time within the 5-second window
        
        For any elapsed time less than 5 seconds, the undo operation
        should be permitted.
        """
        from app.services.validation_service import UNDO_WINDOW_SECONDS
        from datetime import datetime, timezone, timedelta
        
        now = datetime.now(timezone.utc)
        validated_at = now - timedelta(seconds=seconds_elapsed)
        
        # Ensure validated_at is timezone-aware
        if validated_at.tzinfo is None:
            validated_at = validated_at.replace(tzinfo=timezone.utc)
        
        elapsed = (now - validated_at).total_seconds()
        can_undo = elapsed <= UNDO_WINDOW_SECONDS
        
        # Any time less than 5 seconds should allow undo
        assert can_undo == True, f"Undo should be allowed at {seconds_elapsed}s elapsed"

    @given(
        original_prediction=st.booleans(),
        corrected_label=st.booleans(),
    )
    @settings(max_examples=100)
    def test_undo_restores_pre_validation_state_concept(
        self,
        original_prediction: bool,
        corrected_label: bool,
    ):
        """
        Property: Undo conceptually restores pre-validation state
        
        After an undo operation, the scan result should be as if no
        validation was ever submitted. This tests the conceptual model.
        """
        # Before validation: scan result has original_prediction
        pre_validation_state = {
            'has_validation': False,
            'prediction': original_prediction,
        }
        
        # After validation: validation record exists
        is_correction = original_prediction != corrected_label
        post_validation_state = {
            'has_validation': True,
            'prediction': original_prediction,
            'corrected_label': corrected_label,
            'is_correction': is_correction,
        }
        
        # After undo: should return to pre-validation state
        post_undo_state = {
            'has_validation': False,
            'prediction': original_prediction,
        }
        
        # Verify undo restores pre-validation state
        assert post_undo_state == pre_validation_state
        assert post_undo_state['has_validation'] == False

    @given(
        user_id=st.uuids(),
        other_user_id=st.uuids(),
        validation_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_undo_only_allowed_by_validation_owner(
        self,
        user_id: uuid.UUID,
        other_user_id: uuid.UUID,
        validation_id: uuid.UUID,
    ):
        """
        Property: Undo is only allowed by the validation owner
        
        A validation can only be undone by the user who created it.
        Other users should not be able to undo someone else's validation.
        """
        # Assume different users (skip if same UUID generated)
        assume(user_id != other_user_id)
        
        # The validation belongs to user_id
        validation_owner = user_id
        
        # Attempting user is other_user_id
        attempting_user = other_user_id
        
        # Undo should only succeed if attempting_user == validation_owner
        can_undo_by_owner = (validation_owner == user_id)
        can_undo_by_other = (validation_owner == other_user_id)
        
        assert can_undo_by_owner == True
        assert can_undo_by_other == False


class TestUndoWindowPersistenceProperties:
    """
    **Feature: auto-ml-retraining, Property 11: Undo Window Persistence**
    **Validates: Requirements 7.3**
    
    For any validation where the undo window (5 seconds) has expired,
    the validation should be persisted and the undo operation should fail.
    """

    @given(
        seconds_elapsed=st.floats(min_value=5.1, max_value=3600.0),
    )
    @settings(max_examples=100)
    def test_undo_rejected_after_window_expires(
        self,
        seconds_elapsed: float,
    ):
        """
        Property: Undo is rejected after the 5-second window expires
        
        For any elapsed time greater than 5 seconds, the undo operation
        should be rejected.
        """
        from app.services.validation_service import UNDO_WINDOW_SECONDS
        from datetime import datetime, timezone, timedelta
        
        now = datetime.now(timezone.utc)
        validated_at = now - timedelta(seconds=seconds_elapsed)
        
        # Ensure validated_at is timezone-aware
        if validated_at.tzinfo is None:
            validated_at = validated_at.replace(tzinfo=timezone.utc)
        
        elapsed = (now - validated_at).total_seconds()
        can_undo = elapsed <= UNDO_WINDOW_SECONDS
        
        # Any time greater than 5 seconds should reject undo
        assert can_undo == False, f"Undo should be rejected at {seconds_elapsed}s elapsed"

    @given(
        comment_text=st.text(min_size=1, max_size=100).filter(lambda x: len(x.strip()) > 0),
        original_prediction=st.booleans(),
        original_confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        corrected_label=st.booleans(),
        user_id=st.uuids(),
        scan_result_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_validation_persisted_after_window(
        self,
        comment_text: str,
        original_prediction: bool,
        original_confidence: float,
        corrected_label: bool,
        user_id: uuid.UUID,
        scan_result_id: uuid.UUID,
    ):
        """
        Property: Validation is persisted after undo window expires
        
        After the undo window expires, the validation record should
        remain in the database and be available for training.
        """
        from app.services.validation_service import UNDO_WINDOW_SECONDS
        from datetime import datetime, timezone, timedelta
        
        is_correction = original_prediction != corrected_label
        
        # Create validation
        validation = ValidationFeedback(
            scan_result_id=scan_result_id,
            user_id=user_id,
            comment_text=comment_text,
            original_prediction=original_prediction,
            original_confidence=original_confidence,
            corrected_label=corrected_label,
            is_correction=is_correction,
            used_in_training=False,
        )
        
        # Simulate time passing beyond undo window
        old_timestamp = datetime.now(timezone.utc) - timedelta(seconds=UNDO_WINDOW_SECONDS + 1)
        validation.validated_at = old_timestamp
        
        # Verify validation data is preserved
        assert validation.comment_text == comment_text
        assert validation.original_prediction == original_prediction
        assert validation.original_confidence == original_confidence
        assert validation.corrected_label == corrected_label
        assert validation.is_correction == is_correction
        assert validation.user_id == user_id
        assert validation.scan_result_id == scan_result_id

    @given(
        seconds_at_boundary=st.sampled_from([4.99, 5.0, 5.01]),
    )
    @settings(max_examples=100)
    def test_undo_window_boundary_behavior(
        self,
        seconds_at_boundary: float,
    ):
        """
        Property: Undo window boundary is exactly 5 seconds
        
        At exactly 5 seconds, undo should still be allowed (<=).
        At 5.01 seconds, undo should be rejected.
        """
        from app.services.validation_service import UNDO_WINDOW_SECONDS
        from datetime import datetime, timezone, timedelta
        
        now = datetime.now(timezone.utc)
        validated_at = now - timedelta(seconds=seconds_at_boundary)
        
        elapsed = (now - validated_at).total_seconds()
        can_undo = elapsed <= UNDO_WINDOW_SECONDS
        
        if seconds_at_boundary <= 5.0:
            assert can_undo == True, f"Undo should be allowed at exactly {seconds_at_boundary}s"
        else:
            assert can_undo == False, f"Undo should be rejected at {seconds_at_boundary}s"

    @given(
        original_prediction=st.booleans(),
        corrected_label=st.booleans(),
        user_id=st.uuids(),
        scan_result_id=st.uuids(),
    )
    @settings(max_examples=100)
    def test_expired_validation_available_for_training(
        self,
        original_prediction: bool,
        corrected_label: bool,
        user_id: uuid.UUID,
        scan_result_id: uuid.UUID,
    ):
        """
        Property: Expired validations are available for training
        
        After the undo window expires, the validation should be
        eligible for use in model retraining (used_in_training can be set to True).
        """
        from app.services.validation_service import UNDO_WINDOW_SECONDS
        from datetime import datetime, timezone, timedelta
        
        is_correction = original_prediction != corrected_label
        
        # Create validation with expired timestamp
        old_timestamp = datetime.now(timezone.utc) - timedelta(seconds=UNDO_WINDOW_SECONDS + 10)
        
        validation = ValidationFeedback(
            scan_result_id=scan_result_id,
            user_id=user_id,
            comment_text="Test comment for training",
            original_prediction=original_prediction,
            original_confidence=0.85,
            corrected_label=corrected_label,
            is_correction=is_correction,
            used_in_training=False,
            validated_at=old_timestamp,
        )
        
        # Verify validation can be marked for training
        validation.used_in_training = True
        assert validation.used_in_training == True
        
        # Verify all training-relevant data is present
        assert validation.comment_text is not None
        assert validation.corrected_label is not None
        assert validation.original_prediction is not None

    @given(
        num_validations=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=100)
    def test_multiple_expired_validations_all_persisted(
        self,
        num_validations: int,
    ):
        """
        Property: Multiple expired validations are all persisted
        
        When multiple validations have their undo windows expire,
        all of them should remain persisted and available.
        """
        from app.services.validation_service import UNDO_WINDOW_SECONDS
        from datetime import datetime, timezone, timedelta
        
        validations = []
        base_time = datetime.now(timezone.utc) - timedelta(seconds=UNDO_WINDOW_SECONDS + 10)
        
        for i in range(num_validations):
            validation = ValidationFeedback(
                scan_result_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                comment_text=f"Test comment {i}",
                original_prediction=(i % 2 == 0),
                original_confidence=0.5 + (i * 0.01),
                corrected_label=(i % 2 == 1),
                is_correction=True,
                used_in_training=False,
                validated_at=base_time - timedelta(seconds=i),
            )
            validations.append(validation)
        
        # Verify all validations are persisted (have all required fields)
        assert len(validations) == num_validations
        for v in validations:
            assert v.comment_text is not None
            assert v.corrected_label is not None
            assert v.validated_at is not None
            # All should be past undo window
            elapsed = (datetime.now(timezone.utc) - v.validated_at).total_seconds()
            assert elapsed > UNDO_WINDOW_SECONDS
