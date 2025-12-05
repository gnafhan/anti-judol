"""
Property-based tests for the Prediction Service.

Tests correctness properties for ML model predictions and serialization.
"""

import pytest
from hypothesis import given, strategies as st, settings

from app.services.prediction_service import PredictionService
from app.schemas.prediction import PredictionResponse


class TestPredictionOutputFormat:
    """
    **Feature: gambling-comment-detector, Property 3: Prediction Output Format and Bounds**
    **Validates: Requirements 2.2, 2.3, 2.4**
    
    For any list of text strings (1 to 1000 items), the prediction service 
    SHALL return a list of equal length where each prediction contains 
    is_gambling (boolean) and confidence (float between 0.0 and 1.0 inclusive).
    """
    
    @given(
        text=st.text(min_size=1, max_size=500)
    )
    @settings(max_examples=100)
    def test_single_prediction_output_format(self, text: str):
        """Single prediction returns correct format with bounded confidence."""
        service = PredictionService()
        result = service.predict_single(text)
        
        # Verify output structure
        assert "text" in result, "Result must contain 'text' field"
        assert "is_gambling" in result, "Result must contain 'is_gambling' field"
        assert "confidence" in result, "Result must contain 'confidence' field"
        
        # Verify types
        assert isinstance(result["text"], str), "text must be a string"
        assert isinstance(result["is_gambling"], bool), "is_gambling must be a boolean"
        assert isinstance(result["confidence"], float), "confidence must be a float"
        
        # Verify confidence bounds
        assert 0.0 <= result["confidence"] <= 1.0, \
            f"confidence must be between 0.0 and 1.0, got {result['confidence']}"
        
        # Verify text is preserved
        assert result["text"] == text, "Input text must be preserved in output"
    
    @given(
        texts=st.lists(
            st.text(min_size=1, max_size=200),
            min_size=1,
            max_size=50  # Limited for test performance
        )
    )
    @settings(max_examples=100)
    def test_batch_prediction_output_format(self, texts: list[str]):
        """Batch prediction returns correct format with equal length output."""
        service = PredictionService()
        results = service.predict_batch(texts)
        
        # Verify output length matches input
        assert len(results) == len(texts), \
            f"Output length ({len(results)}) must equal input length ({len(texts)})"
        
        # Verify each result
        for i, (result, original_text) in enumerate(zip(results, texts)):
            # Verify output structure
            assert "text" in result, f"Result {i} must contain 'text' field"
            assert "is_gambling" in result, f"Result {i} must contain 'is_gambling' field"
            assert "confidence" in result, f"Result {i} must contain 'confidence' field"
            
            # Verify types
            assert isinstance(result["text"], str), f"Result {i}: text must be a string"
            assert isinstance(result["is_gambling"], bool), f"Result {i}: is_gambling must be a boolean"
            assert isinstance(result["confidence"], float), f"Result {i}: confidence must be a float"
            
            # Verify confidence bounds
            assert 0.0 <= result["confidence"] <= 1.0, \
                f"Result {i}: confidence must be between 0.0 and 1.0, got {result['confidence']}"
            
            # Verify text is preserved
            assert result["text"] == original_text, \
                f"Result {i}: Input text must be preserved in output"
    
    def test_empty_batch_returns_empty_list(self):
        """Empty input list returns empty output list."""
        service = PredictionService()
        results = service.predict_batch([])
        assert results == [], "Empty input should return empty list"


class TestPredictionSerializationRoundTrip:
    """
    **Feature: gambling-comment-detector, Property 4: Prediction Serialization Round-Trip**
    **Validates: Requirements 2.6**
    
    For any PredictionResponse object, serializing to JSON and deserializing 
    back SHALL produce an equivalent object with identical field values.
    """
    
    @given(
        text=st.text(min_size=0, max_size=500),
        is_gambling=st.booleans(),
        confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_prediction_response_serialization_roundtrip(
        self, text: str, is_gambling: bool, confidence: float
    ):
        """PredictionResponse serializes to JSON and deserializes back correctly."""
        # Create original response
        original = PredictionResponse(
            text=text,
            is_gambling=is_gambling,
            confidence=confidence
        )
        
        # Serialize to JSON
        json_str = original.model_dump_json()
        
        # Deserialize back
        restored = PredictionResponse.model_validate_json(json_str)
        
        # Verify round-trip consistency
        assert restored.text == original.text, "text must be preserved after round-trip"
        assert restored.is_gambling == original.is_gambling, "is_gambling must be preserved after round-trip"
        assert abs(restored.confidence - original.confidence) < 1e-10, \
            f"confidence must be preserved after round-trip (original: {original.confidence}, restored: {restored.confidence})"
    
    @given(
        text=st.text(min_size=1, max_size=200)
    )
    @settings(max_examples=100)
    def test_prediction_service_output_serializes_correctly(self, text: str):
        """Prediction service output can be serialized via PredictionResponse schema."""
        service = PredictionService()
        result = service.predict_single(text)
        
        # Create PredictionResponse from service output
        response = PredictionResponse(
            text=result["text"],
            is_gambling=result["is_gambling"],
            confidence=result["confidence"]
        )
        
        # Serialize to JSON
        json_str = response.model_dump_json()
        
        # Deserialize back
        restored = PredictionResponse.model_validate_json(json_str)
        
        # Verify round-trip consistency
        assert restored.text == result["text"]
        assert restored.is_gambling == result["is_gambling"]
        assert abs(restored.confidence - result["confidence"]) < 1e-10
