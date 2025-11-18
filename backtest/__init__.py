"""
Backtesting module for evaluating trading strategies.

This module provides:
- Trade simulation based on signals
- Performance metrics calculation
- Equity curve and drawdown tracking
- Trade history logging
"""

from .backtester import Backtester

__all__ = ["Backtester"]
