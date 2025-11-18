"""
Feature engineering for forex trading ML models.

This module computes technical features and target labels from OHLCV data:
- Returns and lagged returns
- Rolling statistics
- Technical indicators (SMA, RSI, ATR, etc.)
- Target labels for classification

The features are designed to capture:
1. Price momentum and trends
2. Volatility patterns
3. Mean reversion signals
4. Support/resistance levels
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict


class FeatureEngineer:
    """
    Transforms OHLCV data into ML-ready features.

    Attributes:
        lagged_returns (List[int]): Lags for return features (e.g., [1, 3, 5])
        rolling_windows (List[int]): Windows for rolling statistics (e.g., [10, 20, 50])
        indicators (List[str]): Technical indicators to compute
        target_horizon (int): Bars ahead to predict (default: 1)

    Example:
        >>> engineer = FeatureEngineer(
        ...     lagged_returns=[1, 3, 5],
        ...     rolling_windows=[10, 20],
        ...     indicators=["sma", "rsi", "atr"]
        ... )
        >>> df_features = engineer.create_features(df_ohlcv)
        >>> df_with_target = engineer.create_target(df_features)
    """

    def __init__(
        self,
        lagged_returns: List[int] = [1, 3, 5],
        rolling_windows: List[int] = [10, 20, 50],
        indicators: List[str] = ["sma", "rsi", "atr"],
        target_horizon: int = 1
    ):
        """
        Initialize the feature engineer.

        Args:
            lagged_returns: List of lags for return features
            rolling_windows: List of window sizes for rolling stats
            indicators: List of indicator names to compute
            target_horizon: Number of bars ahead to predict
        """
        self.lagged_returns = lagged_returns
        self.rolling_windows = rolling_windows
        self.indicators = indicators
        self.target_horizon = target_horizon

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create all features from OHLCV data.

        Args:
            df: DataFrame with columns [timestamp, open, high, low, close, volume]

        Returns:
            DataFrame with original data + engineered features

        Workflow:
            1. Compute returns
            2. Add lagged returns
            3. Add rolling statistics
            4. Add technical indicators
            5. Handle NaN values
        """
        # TODO: Implement feature creation
        raise NotImplementedError("To be implemented in Phase 2")

    def create_target(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create target variable for classification.

        Target: y = 1 if close[t+horizon] > close[t], else 0

        Args:
            df: DataFrame with OHLCV and features

        Returns:
            DataFrame with 'target' column added
        """
        # TODO: Implement target creation
        raise NotImplementedError("To be implemented in Phase 2")

    def _compute_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute price returns.

        Adds columns:
        - return: (close[t] - close[t-1]) / close[t-1]
        - log_return: log(close[t] / close[t-1])

        Args:
            df: DataFrame with 'close' column

        Returns:
            DataFrame with return columns added
        """
        # TODO: Implement returns calculation
        raise NotImplementedError("To be implemented in Phase 2")

    def _compute_lagged_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute lagged return features.

        For each lag in self.lagged_returns, adds:
        - return_lag_N: return from N bars ago

        Args:
            df: DataFrame with 'return' column

        Returns:
            DataFrame with lagged return columns
        """
        # TODO: Implement lagged returns
        raise NotImplementedError("To be implemented in Phase 2")

    def _compute_rolling_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute rolling mean and standard deviation.

        For each window in self.rolling_windows, adds:
        - return_mean_W: rolling mean of returns over W bars
        - return_std_W: rolling std of returns over W bars

        Args:
            df: DataFrame with 'return' column

        Returns:
            DataFrame with rolling stat columns
        """
        # TODO: Implement rolling statistics
        raise NotImplementedError("To be implemented in Phase 2")

    def _compute_sma(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute Simple Moving Averages.

        For each window in self.rolling_windows, adds:
        - sma_W: simple moving average of close price
        - price_to_sma_W: (close - sma_W) / sma_W (percentage deviation)

        Args:
            df: DataFrame with 'close' column

        Returns:
            DataFrame with SMA columns
        """
        # TODO: Implement SMA calculation
        raise NotImplementedError("To be implemented in Phase 2")

    def _compute_rsi(
        self,
        df: pd.DataFrame,
        period: int = 14
    ) -> pd.DataFrame:
        """
        Compute Relative Strength Index (RSI).

        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss over period

        Args:
            df: DataFrame with 'close' column
            period: RSI period (default: 14)

        Returns:
            DataFrame with 'rsi' column
        """
        # TODO: Implement RSI calculation
        raise NotImplementedError("To be implemented in Phase 2")

    def _compute_atr(
        self,
        df: pd.DataFrame,
        period: int = 14
    ) -> pd.DataFrame:
        """
        Compute Average True Range (ATR).

        True Range = max(high - low, abs(high - prev_close), abs(low - prev_close))
        ATR = rolling mean of True Range over period

        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            period: ATR period (default: 14)

        Returns:
            DataFrame with 'atr' and 'atr_pct' (ATR / close) columns
        """
        # TODO: Implement ATR calculation
        raise NotImplementedError("To be implemented in Phase 2")

    def _handle_missing_values(
        self,
        df: pd.DataFrame,
        method: str = "drop"
    ) -> pd.DataFrame:
        """
        Handle missing values (NaN) in features.

        Args:
            df: DataFrame with features
            method: Method to handle NaN ('drop' or 'fill')

        Returns:
            DataFrame with NaN values handled
        """
        # TODO: Implement NaN handling
        raise NotImplementedError("To be implemented in Phase 2")

    def get_feature_names(self) -> List[str]:
        """
        Get list of all feature column names.

        Returns:
            List of feature column names (excludes timestamp, OHLCV, target)
        """
        # TODO: Implement feature name extraction
        raise NotImplementedError("To be implemented in Phase 2")
