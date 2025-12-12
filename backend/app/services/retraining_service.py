"""
Retraining service for ML model retraining operations.

This service provides:
- Training data combination (original dataset + validation feedback)
- ML pipeline building with hybrid_all_features + LogisticRegression
- Model training and evaluation
- Model deployment and rollback

Requirements: 5.1, 5.3, 6.2, 6.3
"""

import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline, FeatureUnion
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.model_version import ModelVersion
from app.models.validation import ValidationFeedback
from app.ml.preprocessor import TextPreprocessor


settings = get_settings()


class RetrainingError(Exception):
    """Base exception for retraining errors."""
    pass


class InsufficientDataError(RetrainingError):
    """Raised when there's not enough data for retraining."""
    pass


class ModelDeploymentError(RetrainingError):
    """Raised when model deployment fails."""
    pass


class ModelMetrics:
    """Container for model evaluation metrics."""
    
    def __init__(
        self,
        accuracy: float,
        precision: float,
        recall: float,
        f1: float,
        training_samples: int,
        validation_samples: int,
    ):
        self.accuracy = accuracy
        self.precision = precision
        self.recall = recall
        self.f1 = f1
        self.training_samples = training_samples
        self.validation_samples = validation_samples
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "training_samples": self.training_samples,
            "validation_samples": self.validation_samples,
        }


class RetrainingService:
    """
    Retraining service for ML model management.
    
    Implements:
    - Training data combination (Requirements 6.3, 9.3)
    - Pipeline building with hybrid_all_features (Requirements 6.2)
    - Model training and evaluation (Requirements 5.1, 5.3)
    - Model deployment and rollback (Requirements 5.3)
    """
    
    # Default hyperparameters from design document (Requirements 6.2)
    DEFAULT_HYPERPARAMETERS = {
        'classifier__C': 10,
        'classifier__solver': 'lbfgs',
        'vectorizer__word_tfidf__ngram_range': (1, 2),
        'vectorizer__char_tfidf__ngram_range': (2, 4),
    }
    
    def __init__(self, db: AsyncSession):
        """Initialize the retraining service with database session."""
        self.db = db
        self._settings = settings
        self._preprocessor = TextPreprocessor()
        
        # Paths
        self._original_dataset_path = Path(
            getattr(settings, 'original_dataset_path', 'backend/ml/df_all.csv')
        )
        self._model_dir = Path(
            getattr(settings, 'model_dir', 'backend/ml/models')
        )
        self._active_model_path = Path(
            getattr(settings, 'ml_model_path', 'backend/ml/model_pipeline.joblib')
        )
        
        # Hyperparameters (can be overridden via settings)
        self._hyperparameters = self._load_hyperparameters()
        
        # Test size for train/test split
        self._test_size = getattr(settings, 'retraining_test_size', 0.2)
    
    def _load_hyperparameters(self) -> dict[str, Any]:
        """Load hyperparameters from settings or use defaults."""
        hyperparams = self.DEFAULT_HYPERPARAMETERS.copy()
        
        # Override with settings if available
        if hasattr(self._settings, 'classifier_c'):
            hyperparams['classifier__C'] = self._settings.classifier_c
        if hasattr(self._settings, 'classifier_solver'):
            hyperparams['classifier__solver'] = self._settings.classifier_solver
        if hasattr(self._settings, 'word_tfidf_ngram_range'):
            hyperparams['vectorizer__word_tfidf__ngram_range'] = tuple(
                self._settings.word_tfidf_ngram_range
            )
        if hasattr(self._settings, 'char_tfidf_ngram_range'):
            hyperparams['vectorizer__char_tfidf__ngram_range'] = tuple(
                self._settings.char_tfidf_ngram_range
            )
        
        return hyperparams

    async def get_training_data(self) -> pd.DataFrame:
        """
        Get combined training data from original dataset and ALL validation feedback.
        
        Combines df_all.csv with ALL validated user feedback (both used and unused).
        This ensures the dataset always grows and the model is continuously enhanced
        with all historical validations.
        
        Returns:
            DataFrame with 'comment' and 'label' columns
            
        Requirements: 6.3, 9.3
        """
        # Load original dataset
        if not self._original_dataset_path.exists():
            # Try relative path from backend directory
            alt_path = Path('ml/df_all.csv')
            if alt_path.exists():
                self._original_dataset_path = alt_path
            else:
                raise RetrainingError(
                    f"Original dataset not found at {self._original_dataset_path}"
                )
        
        original_df = pd.read_csv(self._original_dataset_path)
        
        # Ensure correct column names
        if 'comment' not in original_df.columns or 'label' not in original_df.columns:
            raise RetrainingError(
                "Original dataset must have 'comment' and 'label' columns"
            )
        
        # Fetch ALL validation feedback (both used and unused)
        # This ensures dataset always grows and model is enhanced with all validations
        result = await self.db.execute(
            select(ValidationFeedback)
        )
        validations = result.scalars().all()
        
        # Convert validation feedback to DataFrame format
        validation_data = []
        for v in validations:
            validation_data.append({
                'comment': v.comment_text,
                'label': 1 if v.corrected_label else 0,  # True=gambling(1), False=clean(0)
            })
        
        if validation_data:
            validation_df = pd.DataFrame(validation_data)
            # Combine datasets
            combined_df = pd.concat([original_df, validation_df], ignore_index=True)
        else:
            combined_df = original_df
        
        # Remove duplicates based on comment text
        combined_df = combined_df.drop_duplicates(subset=['comment'], keep='last')
        
        return combined_df
    
    async def get_unused_validation_count(self) -> int:
        """Get count of validation feedback not yet used in training."""
        from sqlalchemy import func
        
        result = await self.db.execute(
            select(func.count(ValidationFeedback.id)).where(
                ValidationFeedback.used_in_training == False
            )
        )
        return result.scalar() or 0

    async def get_total_validation_count(self) -> int:
        """Get count of ALL validation feedback (used and unused)."""
        from sqlalchemy import func
        
        result = await self.db.execute(
            select(func.count(ValidationFeedback.id))
        )
        return result.scalar() or 0

    async def get_validation_breakdown(self) -> tuple[int, int]:
        """Get breakdown of corrections vs confirmations in pending validations."""
        from sqlalchemy import func
        
        # Corrections count
        corrections_result = await self.db.execute(
            select(func.count(ValidationFeedback.id)).where(
                ValidationFeedback.used_in_training == False,
                ValidationFeedback.is_correction == True,
            )
        )
        corrections = corrections_result.scalar() or 0
        
        # Confirmations count
        confirmations_result = await self.db.execute(
            select(func.count(ValidationFeedback.id)).where(
                ValidationFeedback.used_in_training == False,
                ValidationFeedback.is_correction == False,
            )
        )
        confirmations = confirmations_result.scalar() or 0
        
        return corrections, confirmations

    async def get_original_dataset_size(self) -> int:
        """Get the size of the original training dataset."""
        import pandas as pd
        
        if not self._original_dataset_path.exists():
            alt_path = Path('ml/df_all.csv')
            if alt_path.exists():
                self._original_dataset_path = alt_path
            else:
                return 0
        
        try:
            df = pd.read_csv(self._original_dataset_path)
            return len(df)
        except Exception:
            return 0

    def build_pipeline(self) -> Pipeline:
        """
        Build ML pipeline with hybrid_all_features + LogisticRegression.
        
        Creates a pipeline with:
        - Word-level TF-IDF (ngram_range from settings)
        - Character-level TF-IDF (ngram_range from settings)
        - Logistic Regression classifier (C and solver from settings)
        
        Returns:
            Configured sklearn Pipeline
            
        Requirements: 6.2
        """
        # Extract hyperparameters
        word_ngram = self._hyperparameters.get(
            'vectorizer__word_tfidf__ngram_range', (1, 2)
        )
        char_ngram = self._hyperparameters.get(
            'vectorizer__char_tfidf__ngram_range', (2, 4)
        )
        classifier_c = self._hyperparameters.get('classifier__C', 10)
        classifier_solver = self._hyperparameters.get('classifier__solver', 'lbfgs')
        
        # Build hybrid vectorizer combining word and char n-grams
        vectorizer = FeatureUnion([
            ('word_tfidf', TfidfVectorizer(
                ngram_range=word_ngram,
                analyzer='word',
                max_features=10000,
                preprocessor=self._preprocessor.preprocess,
            )),
            ('char_tfidf', TfidfVectorizer(
                ngram_range=char_ngram,
                analyzer='char',
                max_features=10000,
                preprocessor=self._preprocessor.preprocess,
            )),
        ])
        
        # Build pipeline
        pipeline = Pipeline([
            ('vectorizer', vectorizer),
            ('classifier', LogisticRegression(
                C=classifier_c,
                solver=classifier_solver,
                max_iter=1000,
                random_state=42,
            )),
        ])
        
        return pipeline

    async def train_and_evaluate(
        self,
        data: pd.DataFrame | None = None,
    ) -> tuple[Any, ModelMetrics]:
        """
        Train model and evaluate performance.
        
        Args:
            data: Optional DataFrame with training data. If None, fetches combined data.
            
        Returns:
            Tuple of (trained_model, ModelMetrics)
            
        Requirements: 5.1, 5.3
        """
        # Get training data if not provided
        if data is None:
            data = await self.get_training_data()
        
        # Get validation sample count
        validation_count = await self.get_unused_validation_count()
        
        # Prepare features and labels
        X = data['comment'].values
        y = data['label'].values
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=self._test_size,
            random_state=42,
            stratify=y,
        )
        
        # Build and train pipeline
        pipeline = self.build_pipeline()
        pipeline.fit(X_train, y_train)
        
        # Evaluate
        y_pred = pipeline.predict(X_test)
        
        metrics = ModelMetrics(
            accuracy=accuracy_score(y_test, y_pred),
            precision=precision_score(y_test, y_pred, zero_division=0),
            recall=recall_score(y_test, y_pred, zero_division=0),
            f1=f1_score(y_test, y_pred, zero_division=0),
            training_samples=len(data),
            validation_samples=validation_count,
        )
        
        return pipeline, metrics

    async def deploy_model(
        self,
        model: Any,
        metrics: ModelMetrics,
        version: str | None = None,
    ) -> ModelVersion:
        """
        Deploy a trained model.
        
        Saves the model to disk, creates a ModelVersion record,
        deactivates the previous active model, and activates the new one.
        
        Args:
            model: Trained sklearn pipeline
            metrics: Model evaluation metrics
            version: Optional version string. Auto-generated if not provided.
            
        Returns:
            Created ModelVersion record
            
        Requirements: 5.3
        """
        # Generate version if not provided
        if version is None:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            version = f"v{timestamp}"
        
        # Ensure model directory exists
        self._model_dir.mkdir(parents=True, exist_ok=True)
        
        # Save model to file
        model_filename = f"model_{version}.joblib"
        model_path = self._model_dir / model_filename
        
        try:
            joblib.dump(model, model_path)
        except Exception as e:
            raise ModelDeploymentError(f"Failed to save model: {e}")
        
        # Deactivate current active model
        await self.db.execute(
            update(ModelVersion)
            .where(ModelVersion.is_active == True)
            .values(
                is_active=False,
                deactivated_at=datetime.now(timezone.utc),
            )
        )
        
        # Create new model version record
        model_version = ModelVersion(
            version=version,
            file_path=str(model_path),
            training_samples=metrics.training_samples,
            validation_samples=metrics.validation_samples,
            accuracy=metrics.accuracy,
            precision_score=metrics.precision,
            recall_score=metrics.recall,
            f1_score=metrics.f1,
            is_active=True,
            activated_at=datetime.now(timezone.utc),
        )
        
        self.db.add(model_version)
        await self.db.commit()
        await self.db.refresh(model_version)
        
        # Mark validation feedback as used in training
        await self.db.execute(
            update(ValidationFeedback)
            .where(ValidationFeedback.used_in_training == False)
            .values(
                used_in_training=True,
                model_version_id=model_version.id,
            )
        )
        await self.db.commit()
        
        # Copy to active model path for hot-swap
        try:
            shutil.copy2(model_path, self._active_model_path)
        except Exception as e:
            # Log warning but don't fail - model is saved
            pass
        
        return model_version

    async def rollback_model(self, version_id: uuid.UUID) -> ModelVersion:
        """
        Rollback to a previous model version.
        
        Deactivates the current model and activates the specified version.
        The model will be loaded from the file_path stored in the ModelVersion record.
        
        Args:
            version_id: UUID of the model version to rollback to
            
        Returns:
            The activated ModelVersion record
            
        Requirements: 5.3
        """
        # Fetch the target version
        result = await self.db.execute(
            select(ModelVersion).where(ModelVersion.id == version_id)
        )
        target_version = result.scalar_one_or_none()
        
        if target_version is None:
            raise RetrainingError(f"Model version {version_id} not found")
        
        # Verify model file exists
        model_path = Path(target_version.file_path)
        if not model_path.exists():
            raise RetrainingError(
                f"Model file not found at {target_version.file_path}"
            )
        
        # Deactivate current active model
        await self.db.execute(
            update(ModelVersion)
            .where(ModelVersion.is_active == True)
            .values(
                is_active=False,
                deactivated_at=datetime.now(timezone.utc),
            )
        )
        
        # Activate target version
        target_version.is_active = True
        target_version.activated_at = datetime.now(timezone.utc)
        target_version.deactivated_at = None
        
        await self.db.commit()
        await self.db.refresh(target_version)
        
        # Note: No file copy needed - model is loaded from file_path in the active ModelVersion record
        
        return target_version

    async def get_active_model(self) -> ModelVersion | None:
        """Get the currently active model version."""
        result = await self.db.execute(
            select(ModelVersion).where(ModelVersion.is_active == True)
        )
        return result.scalar_one_or_none()

    async def get_model_versions(self, limit: int = 10) -> list[ModelVersion]:
        """Get recent model versions ordered by creation date."""
        result = await self.db.execute(
            select(ModelVersion)
            .order_by(ModelVersion.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def trigger_retraining(self) -> tuple[ModelVersion, ModelMetrics]:
        """
        Trigger a full retraining cycle.
        
        Combines data, trains model, evaluates, and deploys.
        
        Returns:
            Tuple of (ModelVersion, ModelMetrics)
            
        Requirements: 5.1
        """
        # Get combined training data
        data = await self.get_training_data()
        
        # Check minimum data requirement
        min_samples = getattr(self._settings, 'min_training_samples', 100)
        if len(data) < min_samples:
            raise InsufficientDataError(
                f"Insufficient training data: {len(data)} samples "
                f"(minimum: {min_samples})"
            )
        
        # Train and evaluate
        model, metrics = await self.train_and_evaluate(data)
        
        # Deploy model
        model_version = await self.deploy_model(model, metrics)
        
        return model_version, metrics

    async def get_training_status(self) -> dict[str, Any]:
        """
        Get current training status.
        
        Checks Celery task status for any running retraining jobs.
        
        Returns:
            Dictionary with training status information
        """
        # For now, return a simple status
        # In production, this would check Celery task status
        try:
            from app.workers.celery_app import celery_app
            
            # Check for active retraining tasks
            inspector = celery_app.control.inspect()
            active_tasks = inspector.active() or {}
            
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    if 'retrain' in task.get('name', '').lower():
                        return {
                            "is_training": True,
                            "current_step": "Training in progress",
                            "progress_percent": 50.0,  # Approximate
                            "started_at": task.get('time_start'),
                            "estimated_completion": None,
                            "error_message": None,
                        }
            
            return {
                "is_training": False,
                "current_step": None,
                "progress_percent": 0,
                "started_at": None,
                "estimated_completion": None,
                "error_message": None,
            }
        except Exception:
            # If Celery is not available, return not training
            return {
                "is_training": False,
                "current_step": None,
                "progress_percent": 0,
                "started_at": None,
                "estimated_completion": None,
                "error_message": None,
            }
