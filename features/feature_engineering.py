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
        print(f"Creating features from {len(df)} bars...")

        # Make a copy to avoid modifying original
        df = df.copy()

        # 1. Compute returns
        df = self._compute_returns(df)

        # 2. Compute lagged returns
        df = self._compute_lagged_returns(df)

        # 3. Compute rolling statistics
        df = self._compute_rolling_stats(df)

        # 4. Compute technical indicators
        if "sma" in self.indicators:
            df = self._compute_sma(df)

        if "rsi" in self.indicators:
            df = self._compute_rsi(df)

        if "atr" in self.indicators:
            df = self._compute_atr(df)

        # 5. Handle missing values (drop rows with NaN)
        initial_rows = len(df)
        df = self._handle_missing_values(df, method="drop")

        print(f"✓ Features created: {len(df)} rows after cleaning (dropped {initial_rows - len(df)} rows with NaN)")
        print(f"  Feature columns: {len(self.get_feature_names())}")

        return df

    def create_target(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create target variable for classification.

        Target: y = 1 if close[t+horizon] > close[t], else 0

        Args:
            df: DataFrame with OHLCV and features

        Returns:
            DataFrame with 'target' column added
        """
        print(f"Creating target labels (horizon={self.target_horizon})...")

        df = df.copy()

        # Shift close price by -target_horizon to get future price
        future_close = df['close'].shift(-self.target_horizon)

        # Target: 1 if price goes up, 0 if it goes down
        df['target'] = (future_close > df['close']).astype(int)

        # Drop rows where target is NaN (last target_horizon rows)
        initial_rows = len(df)
        df = df.dropna(subset=['target'])

        # Count target distribution
        target_counts = df['target'].value_counts()
        print(f"✓ Target created: {len(df)} rows (dropped last {initial_rows - len(df)} rows)")
        print(f"  Target distribution: {target_counts.to_dict()}")
        if len(target_counts) > 1:
            print(f"  Balance: {target_counts[1] / len(df) * 100:.1f}% UP, {target_counts[0] / len(df) * 100:.1f}% DOWN")

        return df

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
        df['return'] = df['close'].pct_change()
        df['log_return'] = np.log(df['close'] / df['close'].shift(1))

        return df

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
        for lag in self.lagged_returns:
            df[f'return_lag_{lag}'] = df['return'].shift(lag)

        return df

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
        for window in self.rolling_windows:
            df[f'return_mean_{window}'] = df['return'].rolling(window=window).mean()
            df[f'return_std_{window}'] = df['return'].rolling(window=window).std()

        return df

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
        for window in self.rolling_windows:
            sma = df['close'].rolling(window=window).mean()
            df[f'sma_{window}'] = sma
            df[f'price_to_sma_{window}'] = (df['close'] - sma) / sma

        return df

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
        # Calculate price changes
        delta = df['close'].diff()

        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calculate average gain and loss
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        df['rsi'] = rsi

        return df

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
        # Calculate true range
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift(1))
        low_close = np.abs(df['low'] - df['close'].shift(1))

        # True range is the max of the three
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # ATR is the rolling mean of true range
        atr = true_range.rolling(window=period).mean()

        df['atr'] = atr
        df['atr_pct'] = atr / df['close']  # Normalized ATR

        return df

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
        if method == "drop":
            # Drop rows with any NaN in feature columns
            # Keep timestamp and OHLCV columns even if they have NaN
            feature_cols = self.get_feature_names()

            # Only drop if feature columns have NaN
            if feature_cols:
                df = df.dropna(subset=feature_cols)

            df = df.reset_index(drop=True)

        elif method == "fill":
            # Forward fill then backward fill
            df = df.fillna(method='ffill').fillna(method='bfill')

        return df

    def get_feature_names(self) -> List[str]:
        """
        Get list of all feature column names.

        Returns:
            List of feature column names (excludes timestamp, OHLCV, target)
        """
        exclude_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'target']

        feature_names = []

        # Returns
        feature_names.extend(['return', 'log_return'])

        # Lagged returns
        for lag in self.lagged_returns:
            feature_names.append(f'return_lag_{lag}')

        # Rolling statistics
        for window in self.rolling_windows:
            feature_names.append(f'return_mean_{window}')
            feature_names.append(f'return_std_{window}')

        # SMA
        if "sma" in self.indicators:
            for window in self.rolling_windows:
                feature_names.append(f'sma_{window}')
                feature_names.append(f'price_to_sma_{window}')

        # RSI
        if "rsi" in self.indicators:
            feature_names.append('rsi')

        # ATR
        if "atr" in self.indicators:
            feature_names.append('atr')
            feature_names.append('atr_pct')

        return feature_names
