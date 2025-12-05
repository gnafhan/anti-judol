"""
Prediction service for ML model loading and comment classification.

This service provides:
- Singleton pattern for ML model loading
- Single and batch prediction methods
- Confidence score normalization

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
"""

import joblib
import sys
from pathlib import Path
from typing import Any

# Import custom transformers so they're available for pickle/joblib deserialization
# The ML model was trained with these custom transformers
from app.ml.preprocessor import (
    TextPreprocessor,
    AdditionalFeatures,
    AdditionalFeaturesTransformer,
)

# Register custom transformers in __main__ module for pickle compatibility
# This is needed because the model was pickled with __main__.ClassName
main_module = sys.modules.get('__main__')
if main_module is not None:
    if not hasattr(main_module, 'TextPreprocessor'):
        setattr(main_module, 'TextPreprocessor', TextPreprocessor)
    if not hasattr(main_module, 'AdditionalFeatures'):
        setattr(main_module, 'AdditionalFeatures', AdditionalFeatures)
    if not hasattr(main_module, 'AdditionalFeaturesTransformer'):
        setattr(main_module, 'AdditionalFeaturesTransformer', AdditionalFeaturesTransformer)


class ModelLoadError(Exception):
    """Raised when ML model loading fails."""
    pass


class PredictionService:
    """
    Prediction service for gambling comment classification.
    
    Uses a singleton pattern to load the ML model once and reuse it
    across all prediction requests.
    
    Implements:
    - Model loading with singleton pattern (Requirements 2.1, 2.5)
    - Single and batch prediction (Requirements 2.2, 2.3, 2.4)
    """
    
    _model = None
    _model_path: Path | None = None
    
    @classmethod
    def load_model(cls, model_path: Path | None = None):
        """
        Load ML model from joblib file using singleton pattern.
        
        The model is loaded once and cached for subsequent calls.
        
        Args:
            model_path: Optional custom path to model file.
                       Defaults to backend/ml/model_pipeline.joblib
        
        Returns:
            The loaded scikit-learn pipeline model
            
        Raises:
            ModelLoadError: If model file is missing or corrupted
            
        Requirements: 2.1, 2.5
        """
        if cls._model is not None:
            return cls._model
        
        # Determine model path
        if model_path is None:
            # Default path: backend/ml/model_pipeline.joblib
            model_path = Path(__file__).parent.parent.parent / "ml" / "model_pipeline.joblib"
        
        cls._model_path = model_path
        
        # Check if model file exists
        if not model_path.exists():
            raise ModelLoadError(
                f"ML model file not found at: {model_path}. "
                "Please ensure the model_pipeline.joblib file is present in the backend/ml directory."
            )
        
        try:
            cls._model = joblib.load(model_path)
            return cls._model
        except Exception as e:
            raise ModelLoadError(
                f"Failed to load ML model from {model_path}: {e}. "
                "The model file may be corrupted or incompatible."
            ) from e
    
    @classmethod
    def reset_model(cls):
        """
        Reset the cached model (useful for testing).
        """
        cls._model = None
        cls._model_path = None
    
    def predict_single(self, text: str) -> dict[str, Any]:
        """
        Predict whether a single comment is gambling-related.
        
        Args:
            text: The comment text to classify
            
        Returns:
            Dictionary containing:
            - text: The input text
            - is_gambling: Boolean indicating if gambling content detected
            - confidence: Float between 0.0 and 1.0 indicating model certainty
            
        Requirements: 2.2, 2.4
        """
        model = self.load_model()
        
        # Get prediction (0 = clean, 1 = gambling)
        prediction = model.predict([text])[0]
        
        # Get probability scores
        probabilities = model.predict_proba([text])[0]
        
        # Confidence is the probability of the predicted class
        # Ensure it's bounded between 0.0 and 1.0
        confidence = float(max(0.0, min(1.0, max(probabilities))))
        
        return {
            "text": text,
            "is_gambling": bool(prediction),
            "confidence": confidence
        }
    
    def predict_batch(self, texts: list[str]) -> list[dict[str, Any]]:
        """
        Predict whether multiple comments are gambling-related.
        
        Args:
            texts: List of comment texts to classify (1 to 1000 items)
            
        Returns:
            List of dictionaries, each containing:
            - text: The input text
            - is_gambling: Boolean indicating if gambling content detected
            - confidence: Float between 0.0 and 1.0 indicating model certainty
            
        Requirements: 2.2, 2.3, 2.4
        """
        if not texts:
            return []
        
        model = self.load_model()
        
        # Get predictions for all texts
        predictions = model.predict(texts)
        probabilities = model.predict_proba(texts)
        
        results = []
        for text, pred, prob in zip(texts, predictions, probabilities):
            # Confidence is the probability of the predicted class
            # Ensure it's bounded between 0.0 and 1.0
            confidence = float(max(0.0, min(1.0, max(prob))))
            
            results.append({
                "text": text,
                "is_gambling": bool(pred),
                "confidence": confidence
            })
        
        return results
