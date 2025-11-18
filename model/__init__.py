"""
ML Model module for training and prediction.

This module provides:
- Model training with various algorithms (Logistic Regression, Random Forest, LSTM, KAN)
- Model persistence (save/load)
- Prediction and probability estimation
- Model evaluation metrics
"""

from .train_model import ModelTrainer
from .predict import ModelPredictor

__all__ = ["ModelTrainer", "ModelPredictor"]
