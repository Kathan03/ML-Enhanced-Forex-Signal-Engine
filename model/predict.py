"""
Model prediction and inference for forex signals.

This module handles:
- Loading trained models
- Making predictions on new data
- Probability estimation
- Batch and real-time prediction
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import joblib


class ModelPredictor:
    """
    Makes predictions using trained forex models.

    Attributes:
        model: Trained ML model
        scaler: Feature scaler
        feature_names: List of expected feature names
        model_path: Path to saved model

    Example:
        >>> predictor = ModelPredictor(model_path="models/model.joblib")
        >>> predictor.load_model()
        >>> predictions, probabilities = predictor.predict(X_new)
    """

    def __init__(self, model_path: str = "models/model.joblib"):
        """
        Initialize the model predictor.

        Args:
            model_path: Path to saved model file
        """
        self.model_path = Path(model_path)
        self.model = None
        self.scaler = None
        self.feature_names = []
        self.model_type = None
        self.model_params = {}

    def load_model(self) -> None:
        """
        Load trained model from disk.

        Raises:
            FileNotFoundError: If model file doesn't exist
            ValueError: If loaded model is invalid
        """
        # Check if it's an LSTM model (check for .h5 file)
        h5_file = self.model_path.with_suffix(".h5")
        metadata_file = self.model_path.with_suffix(".metadata")

        if h5_file.exists() and metadata_file.exists():
            # Load LSTM model
            try:
                from tensorflow import keras
            except ImportError:
                raise ImportError(
                    "TensorFlow is required to load LSTM models. "
                    "Install it with: pip install tensorflow"
                )

            self.model = keras.models.load_model(h5_file)
            print(f"✓ LSTM model loaded from: {h5_file}")

            # Load metadata
            metadata = joblib.load(metadata_file)
            self.model_type = metadata["model_type"]
            self.scaler = metadata["scaler"]
            self.feature_names = metadata["feature_names"]
            self.model_params = metadata.get("model_params", {})
            print(f"✓ Metadata loaded from: {metadata_file}")

        elif self.model_path.exists():
            # Load sklearn model
            model_data = joblib.load(self.model_path)

            self.model = model_data["model"]
            self.model_type = model_data["model_type"]
            self.scaler = model_data["scaler"]
            self.feature_names = model_data["feature_names"]
            self.model_params = model_data.get("model_params", {})

            print(f"✓ Model loaded from: {self.model_path}")

        else:
            raise FileNotFoundError(
                f"Model file not found: {self.model_path}\n"
                f"Also checked for LSTM files: {h5_file}, {metadata_file}"
            )

        # Validate model
        if self.model is None:
            raise ValueError("Failed to load model")
        if self.scaler is None:
            raise ValueError("Failed to load scaler")

        print(f"  Model type: {self.model_type}")
        print(f"  Features: {len(self.feature_names)}")

    def predict(
        self,
        X: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Make predictions on new data.

        Args:
            X: DataFrame with features

        Returns:
            Tuple of (predictions, probabilities)
            - predictions: Binary predictions (0 or 1)
            - probabilities: Probability of class 1 (price going up)

        Raises:
            ValueError: If model not loaded or features don't match
        """
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")

        # Validate and scale features
        self._validate_features(X)
        X_scaled = self._scale_features(X)

        # Make predictions based on model type
        if self.model_type in ["logistic_regression", "random_forest"]:
            # Sklearn models
            predictions = self.model.predict(X_scaled)
            probabilities = self.model.predict_proba(X_scaled)[:, 1]

        elif self.model_type == "lstm":
            # LSTM model - need to create sequences
            sequence_length = self.model_params.get("sequence_length", 20)

            if len(X_scaled) < sequence_length:
                raise ValueError(
                    f"Need at least {sequence_length} samples for LSTM prediction, "
                    f"but got {len(X_scaled)}"
                )

            # Create sequences
            X_seq = []
            for i in range(sequence_length - 1, len(X_scaled)):
                X_seq.append(X_scaled[i - sequence_length + 1:i + 1])
            X_seq = np.array(X_seq)

            # Predict
            probabilities = self.model.predict(X_seq).flatten()
            predictions = (probabilities > 0.5).astype(int)

            # Note: For LSTM, predictions are shorter than input by sequence_length - 1
            # We need to pad with NaN for first sequence_length - 1 samples
            full_predictions = np.full(len(X), np.nan)
            full_probabilities = np.full(len(X), np.nan)

            full_predictions[sequence_length - 1:] = predictions
            full_probabilities[sequence_length - 1:] = probabilities

            predictions = full_predictions
            probabilities = full_probabilities

        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        return predictions, probabilities

    def predict_single(
        self,
        features: dict
    ) -> Tuple[int, float]:
        """
        Make prediction for a single observation.

        Args:
            features: Dictionary of feature name -> value

        Returns:
            Tuple of (prediction, probability)

        Example:
            >>> features = {
            ...     'return_lag_1': 0.002,
            ...     'return_lag_3': -0.001,
            ...     'sma_10': 1.0850,
            ...     'rsi': 55.0
            ... }
            >>> pred, prob = predictor.predict_single(features)
        """
        # Convert dict to DataFrame
        df = pd.DataFrame([features])

        # Make prediction
        predictions, probabilities = self.predict(df)

        # Return first (and only) prediction
        pred = predictions[0]
        prob = probabilities[0]

        # Handle NaN (for LSTM when not enough history)
        if np.isnan(pred):
            return None, None

        return int(pred), float(prob)

    def predict_signals(
        self,
        df_features: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generate predictions with metadata for signal generation.

        Args:
            df_features: DataFrame with features and OHLCV data

        Returns:
            DataFrame with columns:
            - timestamp
            - close (price)
            - prediction (0 or 1)
            - probability (0 to 1)

        This is used by the SignalEngine to generate trading signals.
        """
        # Extract feature columns only
        X = df_features[self.feature_names]

        # Make predictions
        predictions, probabilities = self.predict(X)

        # Create result DataFrame
        result = pd.DataFrame({
            'timestamp': df_features['timestamp'],
            'close': df_features['close'],
            'prediction': predictions,
            'probability': probabilities
        })

        return result

    def _validate_features(self, X: pd.DataFrame) -> None:
        """
        Validate that input features match trained model.

        Args:
            X: DataFrame with features

        Raises:
            ValueError: If features don't match expected features
        """
        # Check if all expected features are present
        missing_features = set(self.feature_names) - set(X.columns)
        if missing_features:
            raise ValueError(
                f"Missing features: {missing_features}\n"
                f"Expected features: {self.feature_names}\n"
                f"Got features: {list(X.columns)}"
            )

        # Check for extra features (warning only)
        extra_features = set(X.columns) - set(self.feature_names)
        if extra_features:
            print(f"Warning: Extra features will be ignored: {extra_features}")

    def _scale_features(self, X: pd.DataFrame) -> np.ndarray:
        """
        Scale features using fitted scaler.

        Args:
            X: DataFrame with features

        Returns:
            Scaled feature array
        """
        # Select only the features used during training (in correct order)
        X_selected = X[self.feature_names]

        # Scale features
        X_scaled = self.scaler.transform(X_selected)

        return X_scaled
