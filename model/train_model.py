"""
Model training for forex direction prediction.

This module handles:
- Train/validation/test splitting (time-based)
- Multiple model types (scikit-learn, deep learning)
- Feature scaling and preprocessing
- Model persistence
- Training metrics and evaluation
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report
)
import joblib


class ModelTrainer:
    """
    Trains ML models for forex direction prediction.

    Supports multiple model types:
    - Logistic Regression (baseline)
    - Random Forest
    - LSTM (deep learning)

    Attributes:
        model_type (str): Type of model to train
        model_params (Dict): Hyperparameters for the model
        model_path (Path): Directory to save trained models
        scaler (StandardScaler): Feature scaler

    Example:
        >>> trainer = ModelTrainer(
        ...     model_type="logistic_regression",
        ...     model_params={"C": 1.0, "max_iter": 1000}
        ... )
        >>> trainer.train(X_train, y_train, X_val, y_val)
        >>> trainer.save_model("models/model.joblib")
    """

    def __init__(
        self,
        model_type: str = "logistic_regression",
        model_params: Optional[Dict[str, Any]] = None,
        model_path: str = "models",
        random_state: int = 42
    ):
        """
        Initialize the model trainer.

        Args:
            model_type: Type of model ('logistic_regression', 'random_forest', 'lstm', 'kan')
            model_params: Model hyperparameters
            model_path: Directory for saving models
            random_state: Random seed for reproducibility
        """
        self.model_type = model_type
        self.model_params = model_params or {}
        self.model_path = Path(model_path)
        self.random_state = random_state

        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.training_metrics = {}

        # Create model directory
        self.model_path.mkdir(parents=True, exist_ok=True)

    def prepare_data(
        self,
        df: pd.DataFrame,
        feature_cols: list,
        target_col: str = "target",
        train_ratio: float = 0.8
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Prepare data for training with time-based split.

        Args:
            df: DataFrame with features and target
            feature_cols: List of feature column names
            target_col: Target column name
            train_ratio: Ratio of data to use for training

        Returns:
            Tuple of (X_train, X_val, y_train, y_val)
        """
        # Store feature names
        self.feature_names = feature_cols

        # Time-based split (no shuffling for time series)
        split_idx = int(len(df) * train_ratio)

        train_df = df.iloc[:split_idx]
        val_df = df.iloc[split_idx:]

        # Separate features and target
        X_train = train_df[feature_cols]
        y_train = train_df[target_col]
        X_val = val_df[feature_cols]
        y_val = val_df[target_col]

        print(f"Data split:")
        print(f"  Training set: {len(X_train)} samples")
        print(f"  Validation set: {len(X_val)} samples")
        print(f"  Features: {len(feature_cols)}")

        return X_train, X_val, y_train, y_val

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None
    ) -> Dict[str, float]:
        """
        Train the ML model.

        Args:
            X_train: Training features
            y_train: Training target
            X_val: Validation features (optional)
            y_val: Validation target (optional)

        Returns:
            Dictionary of training metrics

        Workflow:
            1. Scale features
            2. Initialize model based on type
            3. Train model
            4. Evaluate on validation set
            5. Store metrics
        """
        print(f"\nTraining {self.model_type} model...")

        # 1. Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        if X_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
        else:
            X_val_scaled = None

        # Convert to numpy arrays
        y_train_arr = y_train.values

        # 2. Initialize model
        self._init_model()

        # 3. Train model
        if self.model_type in ["logistic_regression", "random_forest"]:
            self._train_sklearn_model(X_train_scaled, y_train_arr)
        elif self.model_type == "lstm":
            if X_val_scaled is None:
                raise ValueError("Validation data is required for LSTM training")
            y_val_arr = y_val.values
            self._train_lstm_model(X_train_scaled, y_train_arr, X_val_scaled, y_val_arr)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        # 4. Evaluate on validation set
        if X_val is not None and y_val is not None:
            metrics = self.evaluate(X_val, y_val)
            self.training_metrics = metrics

            print(f"\nValidation Metrics:")
            for metric, value in metrics.items():
                print(f"  {metric}: {value:.4f}")

            return metrics
        else:
            print("No validation data provided, skipping evaluation")
            return {}

    def _init_model(self):
        """
        Initialize model based on model_type.

        Returns:
            Initialized model object

        Raises:
            ValueError: If model_type is not supported
        """
        if self.model_type == "logistic_regression":
            default_params = {
                "C": 1.0,
                "max_iter": 1000,
                "random_state": self.random_state,
                "solver": "lbfgs"
            }
            params = {**default_params, **self.model_params}
            self.model = LogisticRegression(**params)
            print(f"  Initialized Logistic Regression with params: {params}")

        elif self.model_type == "random_forest":
            default_params = {
                "n_estimators": 100,
                "max_depth": 10,
                "min_samples_split": 5,
                "random_state": self.random_state,
                "n_jobs": -1
            }
            params = {**default_params, **self.model_params}
            self.model = RandomForestClassifier(**params)
            print(f"  Initialized Random Forest with params: {params}")

        elif self.model_type == "lstm":
            # LSTM model will be created in _train_lstm_model
            # after we know the input shape from sequences
            self.model = None
            print(f"  LSTM model will be created during training")

        else:
            raise ValueError(
                f"Unsupported model type: {self.model_type}. "
                f"Supported: logistic_regression, random_forest, lstm"
            )

    def _train_sklearn_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray
    ):
        """
        Train scikit-learn model (Logistic Regression or Random Forest).

        Args:
            X_train: Training features (scaled)
            y_train: Training target
        """
        print(f"  Training {self.model_type}...")

        # Train model
        self.model.fit(X_train, y_train)

        # Get training accuracy
        train_pred = self.model.predict(X_train)
        train_acc = accuracy_score(y_train, train_pred)

        print(f"  Training accuracy: {train_acc:.4f}")
        print(f"  Model trained successfully!")

    def _train_lstm_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None
    ):
        """
        Train LSTM model using TensorFlow/Keras.

        Args:
            X_train: Training features
            y_train: Training target
            X_val: Validation features
            y_val: Validation target
        """
        try:
            from tensorflow import keras
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dense, Dropout
            from tensorflow.keras.callbacks import EarlyStopping
        except ImportError:
            raise ImportError(
                "TensorFlow is required for LSTM training. "
                "Install it with: pip install tensorflow"
            )

        print(f"  Preparing sequences for LSTM...")

        # Get sequence length from params (default 20)
        sequence_length = self.model_params.get("sequence_length", 20)

        # Create sequences
        X_train_seq, y_train_seq = self._create_sequences(X_train, y_train, sequence_length)
        X_val_seq, y_val_seq = self._create_sequences(X_val, y_val, sequence_length)

        print(f"  Sequence shape: {X_train_seq.shape}")
        print(f"  Training samples: {len(X_train_seq)}")
        print(f"  Validation samples: {len(X_val_seq)}")

        # Build LSTM model
        print(f"  Building LSTM architecture...")

        n_features = X_train_seq.shape[2]

        # Get architecture params
        lstm_units = self.model_params.get("lstm_units", 50)
        dropout_rate = self.model_params.get("dropout", 0.2)
        epochs = self.model_params.get("epochs", 50)
        batch_size = self.model_params.get("batch_size", 32)

        self.model = Sequential([
            LSTM(lstm_units, activation='tanh', return_sequences=True,
                 input_shape=(sequence_length, n_features)),
            Dropout(dropout_rate),
            LSTM(lstm_units // 2, activation='tanh'),
            Dropout(dropout_rate),
            Dense(1, activation='sigmoid')
        ])

        self.model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )

        print(f"  Model architecture:")
        self.model.summary()

        # Early stopping callback
        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True,
            verbose=1
        )

        # Train model
        print(f"\n  Training LSTM for up to {epochs} epochs...")

        history = self.model.fit(
            X_train_seq, y_train_seq,
            validation_data=(X_val_seq, y_val_seq),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stop],
            verbose=1
        )

        # Store training history
        self.training_history = history.history

        print(f"\n  LSTM training completed!")
        print(f"  Best validation accuracy: {max(history.history['val_accuracy']):.4f}")

    def _create_sequences(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sequence_length: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for LSTM training.

        Converts data into sliding window sequences:
        - For each timestep t, create a sequence of length `sequence_length`
          using data from [t-sequence_length+1, t]
        - The target is y[t]

        Args:
            X: Feature array (n_samples, n_features)
            y: Target array (n_samples,)
            sequence_length: Number of timesteps per sequence

        Returns:
            Tuple of (X_sequences, y_sequences)
            - X_sequences: (n_samples - sequence_length + 1, sequence_length, n_features)
            - y_sequences: (n_samples - sequence_length + 1,)
        """
        X_seq = []
        y_seq = []

        for i in range(sequence_length, len(X) + 1):
            # Extract sequence from [i-sequence_length:i]
            X_seq.append(X[i - sequence_length:i])
            # Target is the label at position i-1 (last element of sequence)
            y_seq.append(y[i - 1])

        return np.array(X_seq), np.array(y_seq)

    def evaluate(
        self,
        X: pd.DataFrame,
        y: pd.Series
    ) -> Dict[str, float]:
        """
        Evaluate model performance.

        Args:
            X: Features
            y: True labels

        Returns:
            Dictionary of metrics (accuracy, precision, recall, F1, AUC)
        """
        # Scale features
        X_scaled = self.scaler.transform(X)
        y_true = y.values

        # Make predictions
        if self.model_type in ["logistic_regression", "random_forest"]:
            y_pred = self.model.predict(X_scaled)
            y_pred_proba = self.model.predict_proba(X_scaled)[:, 1]

        elif self.model_type == "lstm":
            # Create sequences for LSTM
            sequence_length = self.model_params.get("sequence_length", 20)
            X_seq, y_seq = self._create_sequences(X_scaled, y_true, sequence_length)

            # Predict
            y_pred_proba_seq = self.model.predict(X_seq).flatten()
            y_pred = (y_pred_proba_seq > 0.5).astype(int)

            # Update to use sequence-aligned labels
            y_true = y_seq
            y_pred_proba = y_pred_proba_seq

        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        # Calculate metrics
        metrics = {
            "accuracy": accuracy_score(y_true, y_pred),
            "precision": precision_score(y_true, y_pred, zero_division=0),
            "recall": recall_score(y_true, y_pred, zero_division=0),
            "f1": f1_score(y_true, y_pred, zero_division=0),
            "roc_auc": roc_auc_score(y_true, y_pred_proba)
        }

        return metrics

    def save_model(self, filename: str = "model.joblib") -> None:
        """
        Save trained model and scaler to disk.

        Saves:
        - Trained model
        - Feature scaler
        - Feature names
        - Training metrics

        Args:
            filename: Name of the file to save
        """
        if self.model is None:
            raise ValueError("No trained model to save. Train a model first.")

        filepath = self.model_path / filename

        # For LSTM, save model separately
        if self.model_type == "lstm":
            # Save Keras model as .h5
            model_file = filepath.with_suffix(".h5")
            self.model.save(model_file)
            print(f"✓ LSTM model saved to: {model_file}")

            # Save metadata (scaler, feature names, metrics, params)
            metadata = {
                "model_type": self.model_type,
                "scaler": self.scaler,
                "feature_names": self.feature_names,
                "training_metrics": self.training_metrics,
                "model_params": self.model_params,
                "random_state": self.random_state
            }
            metadata_file = filepath.with_suffix(".metadata")
            joblib.dump(metadata, metadata_file)
            print(f"✓ Metadata saved to: {metadata_file}")

        else:
            # For sklearn models, save everything together
            model_data = {
                "model": self.model,
                "model_type": self.model_type,
                "scaler": self.scaler,
                "feature_names": self.feature_names,
                "training_metrics": self.training_metrics,
                "model_params": self.model_params,
                "random_state": self.random_state
            }
            joblib.dump(model_data, filepath)
            print(f"✓ Model saved to: {filepath}")

    def load_model(self, filename: str = "model.joblib") -> None:
        """
        Load trained model from disk.

        Args:
            filename: Name of the file to load

        Raises:
            FileNotFoundError: If model file doesn't exist
        """
        filepath = self.model_path / filename

        # Check if it's an LSTM model (check for .h5 file)
        h5_file = filepath.with_suffix(".h5")
        metadata_file = filepath.with_suffix(".metadata")

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
            self.training_metrics = metadata["training_metrics"]
            self.model_params = metadata["model_params"]
            self.random_state = metadata["random_state"]
            print(f"✓ Metadata loaded from: {metadata_file}")

        elif filepath.exists():
            # Load sklearn model
            model_data = joblib.load(filepath)

            self.model = model_data["model"]
            self.model_type = model_data["model_type"]
            self.scaler = model_data["scaler"]
            self.feature_names = model_data["feature_names"]
            self.training_metrics = model_data["training_metrics"]
            self.model_params = model_data["model_params"]
            self.random_state = model_data["random_state"]

            print(f"✓ Model loaded from: {filepath}")

        else:
            raise FileNotFoundError(
                f"Model file not found: {filepath}\n"
                f"Also checked for LSTM files: {h5_file}, {metadata_file}"
            )

    def get_feature_importance(self) -> Optional[pd.DataFrame]:
        """
        Get feature importance (for tree-based models).

        Returns:
            DataFrame with feature names and importance scores,
            or None if model doesn't support feature importance
        """
        if self.model is None:
            raise ValueError("No trained model available")

        if self.model_type == "random_forest":
            # Get feature importance from Random Forest
            importance = self.model.feature_importances_

            # Create DataFrame
            importance_df = pd.DataFrame({
                "feature": self.feature_names,
                "importance": importance
            })

            # Sort by importance
            importance_df = importance_df.sort_values("importance", ascending=False)
            importance_df = importance_df.reset_index(drop=True)

            return importance_df

        elif self.model_type == "logistic_regression":
            # Get coefficients (absolute values as proxy for importance)
            coef = np.abs(self.model.coef_[0])

            importance_df = pd.DataFrame({
                "feature": self.feature_names,
                "importance": coef
            })

            # Sort by importance
            importance_df = importance_df.sort_values("importance", ascending=False)
            importance_df = importance_df.reset_index(drop=True)

            return importance_df

        else:
            # LSTM doesn't have feature importance
            print(f"Feature importance not available for {self.model_type}")
            return None
