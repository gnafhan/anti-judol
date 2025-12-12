"""
Prediction service for ML model loading and comment classification.

This service provides:
- Singleton pattern for ML model loading
- Single and batch prediction methods
- Confidence score normalization
- Thread-safe model hot-swap for retraining

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 5.2, 5.3
"""

import joblib
import logging
import sys
import threading
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


logger = logging.getLogger(__name__)


class ModelLoadError(Exception):
    """Raised when ML model loading fails."""
    pass


class PredictionService:
    """
    Prediction service for gambling comment classification.
    
    Uses a singleton pattern to load the ML model once and reuse it
    across all prediction requests. Supports thread-safe model hot-swap
    for retraining without service restart.
    
    Implements:
    - Model loading with singleton pattern (Requirements 2.1, 2.5)
    - Single and batch prediction (Requirements 2.2, 2.3, 2.4)
    - Thread-safe model hot-swap (Requirements 5.2, 5.3)
    """
    
    _model = None
    _model_path: Path | None = None
    _model_lock = threading.RLock()  # Reentrant lock for thread-safe model access
    _is_reloading = False  # Flag to track reload state
    
    @classmethod
    def load_model(cls, model_path: Path | None = None):
        """
        Load ML model from joblib file using singleton pattern.
        
        The model is loaded once and cached for subsequent calls.
        Thread-safe: uses lock to prevent concurrent loading.
        
        Args:
            model_path: Optional custom path to model file.
                       Defaults to backend/ml/model_pipeline.joblib
        
        Returns:
            The loaded scikit-learn pipeline model
            
        Raises:
            ModelLoadError: If model file is missing or corrupted
            
        Requirements: 2.1, 2.5
        """
        with cls._model_lock:
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
                logger.info(f"ML model loaded from {model_path}")
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
        Thread-safe: uses lock to prevent concurrent access.
        """
        with cls._model_lock:
            cls._model = None
            cls._model_path = None
    
    @classmethod
    def reload_model(cls, model_path: Path | None = None) -> bool:
        """
        Reload the ML model without service restart (hot-swap).
        
        Thread-safe: The current model continues serving predictions
        while the new model is being loaded. Only after successful
        loading is the model reference swapped atomically.
        
        Args:
            model_path: Optional custom path to model file.
                       If None, reloads from the current model path.
        
        Returns:
            True if reload was successful, False otherwise
            
        Requirements: 5.2, 5.3
        """
        with cls._model_lock:
            if cls._is_reloading:
                logger.warning("Model reload already in progress, skipping")
                return False
            
            cls._is_reloading = True
        
        try:
            # Determine the path to load from
            if model_path is None:
                if cls._model_path is not None:
                    model_path = cls._model_path
                else:
                    model_path = Path(__file__).parent.parent.parent / "ml" / "model_pipeline.joblib"
            
            # Check if model file exists
            if not model_path.exists():
                logger.error(f"Model file not found at {model_path}")
                return False
            
            # Load new model (outside the lock to allow concurrent predictions)
            try:
                new_model = joblib.load(model_path)
                logger.info(f"New model loaded from {model_path}")
            except Exception as e:
                logger.error(f"Failed to load new model from {model_path}: {e}")
                return False
            
            # Atomically swap the model reference
            with cls._model_lock:
                old_model = cls._model
                cls._model = new_model
                cls._model_path = model_path
                logger.info("Model hot-swap completed successfully")
            
            # Old model will be garbage collected
            del old_model
            
            return True
            
        finally:
            with cls._model_lock:
                cls._is_reloading = False
    
    @classmethod
    def is_model_loaded(cls) -> bool:
        """Check if a model is currently loaded."""
        with cls._model_lock:
            return cls._model is not None
    
    @classmethod
    def get_model_path(cls) -> Path | None:
        """Get the current model path."""
        with cls._model_lock:
            return cls._model_path
    
    def predict_single(self, text: str) -> dict[str, Any]:
        """
        Predict whether a single comment is gambling-related.
        
        Thread-safe: Uses lock to ensure model is not swapped during prediction.
        The model continues serving predictions during retraining (Requirement 5.2).
        
        Args:
            text: The comment text to classify
            
        Returns:
            Dictionary containing:
            - text: The input text
            - is_gambling: Boolean indicating if gambling content detected
            - confidence: Float between 0.0 and 1.0 indicating model certainty
            
        Requirements: 2.2, 2.4, 5.2
        """
        # Get model reference under lock, then release for prediction
        with self._model_lock:
            model = self.load_model()
        
        # Prediction happens outside lock to allow concurrent predictions
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
        
        Thread-safe: Uses lock to ensure model is not swapped during prediction.
        The model continues serving predictions during retraining (Requirement 5.2).
        
        Args:
            texts: List of comment texts to classify (1 to 1000 items)
            
        Returns:
            List of dictionaries, each containing:
            - text: The input text
            - is_gambling: Boolean indicating if gambling content detected
            - confidence: Float between 0.0 and 1.0 indicating model certainty
            
        Requirements: 2.2, 2.3, 2.4, 5.2
        """
        if not texts:
            return []
        
        # Get model reference under lock, then release for prediction
        with self._model_lock:
            model = self.load_model()
        
        # Prediction happens outside lock to allow concurrent predictions
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
