"""
Signal engine for generating EA-style trading signals.

This module converts ML model predictions into structured trading signals
with stop loss, take profit, and confidence scores.

Signal format matches Expert Advisor (EA) expectations:
{
    "timestamp": "2024-01-15 10:00:00",
    "symbol": "EURUSD",
    "signal": "BUY",
    "entry_price": 1.0850,
    "stop_loss": 1.0830,
    "take_profit": 1.0890,
    "confidence": 0.74
}
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import json


class SignalEngine:
    """
    Generates EA-style trading signals from ML predictions.

    Signal Logic:
    - probability > buy_threshold → BUY
    - probability < sell_threshold → SELL
    - else → FLAT (no trade)

    Risk Management:
    - Stop Loss: entry_price ± (ATR × sl_multiplier)
    - Take Profit: entry_price ± (ATR × tp_multiplier)

    Attributes:
        buy_threshold (float): Probability threshold for BUY signal
        sell_threshold (float): Probability threshold for SELL signal
        sl_multiplier (float): ATR multiplier for stop loss
        tp_multiplier (float): ATR multiplier for take profit
        symbol (str): Forex pair symbol

    Example:
        >>> engine = SignalEngine(
        ...     buy_threshold=0.6,
        ...     sell_threshold=0.4,
        ...     sl_multiplier=2.0,
        ...     tp_multiplier=3.0
        ... )
        >>> signals = engine.generate_signals(df_predictions)
        >>> engine.export_signals(signals, format="json")
    """

    def __init__(
        self,
        buy_threshold: float = 0.6,
        sell_threshold: float = 0.4,
        sl_multiplier: float = 2.0,
        tp_multiplier: float = 3.0,
        symbol: str = "EURUSD",
        output_path: str = "outputs"
    ):
        """
        Initialize the signal engine.

        Args:
            buy_threshold: Probability threshold for BUY (e.g., 0.6 means P(up) > 60%)
            sell_threshold: Probability threshold for SELL (e.g., 0.4 means P(up) < 40%)
            sl_multiplier: Stop loss distance as multiple of ATR
            tp_multiplier: Take profit distance as multiple of ATR
            symbol: Forex pair symbol
            output_path: Directory for signal outputs
        """
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.sl_multiplier = sl_multiplier
        self.tp_multiplier = tp_multiplier
        self.symbol = symbol
        self.output_path = Path(output_path)

        # Create output directory
        self.output_path.mkdir(parents=True, exist_ok=True)

    def generate_signals(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generate trading signals from predictions and OHLCV data.

        Args:
            df: DataFrame with columns:
                - timestamp
                - close (current price)
                - atr (Average True Range)
                - prediction (0 or 1)
                - probability (0 to 1)

        Returns:
            DataFrame with columns:
                - timestamp
                - symbol
                - signal (BUY/SELL/FLAT)
                - entry_price
                - stop_loss
                - take_profit
                - confidence
        """
        print(f"Generating signals for {len(df)} bars...")

        signals = []

        for idx, row in df.iterrows():
            # Skip rows with NaN predictions (e.g., LSTM initial sequence)
            if pd.isna(row['probability']):
                continue

            # Determine signal type
            signal_type = self._determine_signal(row['probability'])

            # Entry price is the close price
            entry_price = row['close']

            # Get ATR (use default if not available)
            atr = row.get('atr', 0.002 * entry_price)  # Default 20 pips for EURUSD

            # Calculate SL/TP
            stop_loss, take_profit = self._calculate_sl_tp(signal_type, entry_price, atr)

            # Confidence is the probability (for BUY) or 1-probability (for SELL)
            if signal_type == "BUY":
                confidence = row['probability']
            elif signal_type == "SELL":
                confidence = 1 - row['probability']
            else:  # FLAT
                confidence = 0.5  # Neutral

            signals.append({
                'timestamp': row['timestamp'],
                'symbol': self.symbol,
                'signal': signal_type,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'confidence': confidence
            })

        signals_df = pd.DataFrame(signals)

        print(f"✓ Generated {len(signals_df)} signals")
        return signals_df

    def _determine_signal(self, probability: float) -> str:
        """
        Determine signal type based on probability thresholds.

        Args:
            probability: Predicted probability of price going up

        Returns:
            Signal string: "BUY", "SELL", or "FLAT"
        """
        if probability > self.buy_threshold:
            return "BUY"
        elif probability < self.sell_threshold:
            return "SELL"
        else:
            return "FLAT"

    def _calculate_sl_tp(
        self,
        signal: str,
        entry_price: float,
        atr: float
    ) -> tuple:
        """
        Calculate stop loss and take profit levels.

        For BUY:
        - Stop Loss: entry_price - (atr × sl_multiplier)
        - Take Profit: entry_price + (atr × tp_multiplier)

        For SELL:
        - Stop Loss: entry_price + (atr × sl_multiplier)
        - Take Profit: entry_price - (atr × tp_multiplier)

        For FLAT:
        - Both are None

        Args:
            signal: Signal type (BUY/SELL/FLAT)
            entry_price: Entry price
            atr: Average True Range

        Returns:
            Tuple of (stop_loss, take_profit)
        """
        if signal == "BUY":
            stop_loss = entry_price - (atr * self.sl_multiplier)
            take_profit = entry_price + (atr * self.tp_multiplier)
        elif signal == "SELL":
            stop_loss = entry_price + (atr * self.sl_multiplier)
            take_profit = entry_price - (atr * self.tp_multiplier)
        else:  # FLAT
            stop_loss = None
            take_profit = None

        return stop_loss, take_profit

    def export_signals(
        self,
        signals: pd.DataFrame,
        filename: str = "signals",
        format: str = "both"
    ) -> None:
        """
        Export signals to CSV and/or JSON.

        Args:
            signals: DataFrame with signals
            filename: Base filename (without extension)
            format: Output format ("csv", "json", or "both")
        """
        print(f"\nExporting signals (format: {format})...")

        if format in ["csv", "both"]:
            csv_path = self.output_path / f"{filename}.csv"
            self._export_to_csv(signals, csv_path)

        if format in ["json", "both"]:
            json_path = self.output_path / f"{filename}.json"
            self._export_to_json(signals, json_path)

        print(f"✓ Signals exported successfully")

    def _export_to_csv(
        self,
        signals: pd.DataFrame,
        filepath: Path
    ) -> None:
        """
        Export signals to CSV file.

        Args:
            signals: DataFrame with signals
            filepath: Full path to CSV file
        """
        signals.to_csv(filepath, index=False)
        print(f"  ✓ CSV saved to: {filepath}")

    def _export_to_json(
        self,
        signals: pd.DataFrame,
        filepath: Path
    ) -> None:
        """
        Export signals to JSON file.

        Format: Array of signal objects

        Args:
            signals: DataFrame with signals
            filepath: Full path to JSON file
        """
        # Convert timestamp to string for JSON serialization
        signals_copy = signals.copy()
        signals_copy['timestamp'] = signals_copy['timestamp'].astype(str)

        # Convert to list of dictionaries
        signals_list = signals_copy.to_dict('records')

        # Write to JSON file
        with open(filepath, 'w') as f:
            json.dump(signals_list, f, indent=2)

        print(f"  ✓ JSON saved to: {filepath}")

    def filter_signals(
        self,
        signals: pd.DataFrame,
        min_confidence: float = 0.0,
        exclude_flat: bool = True
    ) -> pd.DataFrame:
        """
        Filter signals based on criteria.

        Args:
            signals: DataFrame with signals
            min_confidence: Minimum confidence threshold
            exclude_flat: If True, remove FLAT signals

        Returns:
            Filtered signals DataFrame
        """
        filtered = signals.copy()

        # Filter by confidence
        if min_confidence > 0.0:
            filtered = filtered[filtered['confidence'] >= min_confidence]

        # Exclude FLAT signals
        if exclude_flat:
            filtered = filtered[filtered['signal'] != 'FLAT']

        return filtered

    def get_signal_statistics(
        self,
        signals: pd.DataFrame
    ) -> Dict:
        """
        Compute statistics about generated signals.

        Returns:
            Dictionary with:
            - total_signals
            - buy_count
            - sell_count
            - flat_count
            - avg_confidence
        """
        stats = {
            'total_signals': len(signals),
            'buy_count': len(signals[signals['signal'] == 'BUY']),
            'sell_count': len(signals[signals['signal'] == 'SELL']),
            'flat_count': len(signals[signals['signal'] == 'FLAT']),
            'avg_confidence': signals['confidence'].mean()
        }

        # Calculate percentages
        if stats['total_signals'] > 0:
            stats['buy_pct'] = (stats['buy_count'] / stats['total_signals']) * 100
            stats['sell_pct'] = (stats['sell_count'] / stats['total_signals']) * 100
            stats['flat_pct'] = (stats['flat_count'] / stats['total_signals']) * 100
        else:
            stats['buy_pct'] = 0.0
            stats['sell_pct'] = 0.0
            stats['flat_pct'] = 0.0

        return stats
