"""
Metrics calculation utilities for backtesting and model evaluation.

This module provides reusable functions for:
- Trading performance metrics
- ML model evaluation metrics
- Risk metrics
"""

import pandas as pd
import numpy as np
from typing import List, Dict


class MetricsCalculator:
    """
    Calculates various trading and ML metrics.

    Example:
        >>> calc = MetricsCalculator()
        >>> sharpe = calc.sharpe_ratio(returns)
        >>> drawdown = calc.max_drawdown(equity_curve)
    """

    @staticmethod
    def sharpe_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate annualized Sharpe ratio.

        Args:
            returns: Series of returns
            risk_free_rate: Annual risk-free rate
            periods_per_year: Trading periods per year

        Returns:
            Sharpe ratio
        """
        if len(returns) == 0 or returns.std() == 0:
            return 0.0

        excess_returns = returns - (risk_free_rate / periods_per_year)
        return np.sqrt(periods_per_year) * excess_returns.mean() / returns.std()

    @staticmethod
    def max_drawdown(equity_curve: pd.Series) -> float:
        """
        Calculate maximum drawdown.

        Args:
            equity_curve: Series of equity values

        Returns:
            Maximum drawdown (absolute value)
        """
        if len(equity_curve) == 0:
            return 0.0

        peak = equity_curve.expanding(min_periods=1).max()
        drawdown = equity_curve - peak
        return abs(drawdown.min())

    @staticmethod
    def max_drawdown_pct(equity_curve: pd.Series) -> float:
        """
        Calculate maximum drawdown percentage.

        Args:
            equity_curve: Series of equity values

        Returns:
            Maximum drawdown as percentage
        """
        if len(equity_curve) == 0:
            return 0.0

        peak = equity_curve.expanding(min_periods=1).max()
        drawdown_pct = (equity_curve - peak) / peak * 100
        return abs(drawdown_pct.min())

    @staticmethod
    def win_rate(trades: List[Dict]) -> float:
        """
        Calculate win rate from trades.

        Args:
            trades: List of trade dictionaries with 'pnl' key

        Returns:
            Win rate as percentage
        """
        if len(trades) == 0:
            return 0.0

        wins = sum(1 for t in trades if t.get('pnl', 0) > 0)
        return (wins / len(trades)) * 100

    @staticmethod
    def profit_factor(trades: List[Dict]) -> float:
        """
        Calculate profit factor.

        Profit Factor = Gross Profit / Gross Loss

        Args:
            trades: List of trade dictionaries with 'pnl' key

        Returns:
            Profit factor
        """
        if len(trades) == 0:
            return 0.0

        gross_profit = sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0)
        gross_loss = abs(sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0))

        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0

        return gross_profit / gross_loss

    @staticmethod
    def average_win_loss(trades: List[Dict]) -> tuple:
        """
        Calculate average win and average loss.

        Args:
            trades: List of trade dictionaries with 'pnl' key

        Returns:
            Tuple of (avg_win, avg_loss)
        """
        if len(trades) == 0:
            return (0.0, 0.0)

        wins = [t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0]
        losses = [t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0]

        avg_win = np.mean(wins) if wins else 0.0
        avg_loss = np.mean(losses) if losses else 0.0

        return (avg_win, avg_loss)
