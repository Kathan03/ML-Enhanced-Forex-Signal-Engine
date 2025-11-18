"""
Feature engineering module for ML model training.

This module transforms raw OHLCV data into features suitable for ML models:
- Price returns and lagged features
- Rolling statistics (mean, std, volatility)
- Technical indicators (SMA, RSI, ATR)
- Target label generation
"""

from .feature_engineering import FeatureEngineer

__all__ = ["FeatureEngineer"]
