"""
Signal generation module for EA-style trading signals.

This module converts ML predictions into actionable trading signals:
- BUY/SELL/FLAT signal generation
- Stop loss and take profit calculation
- Confidence scoring
- Signal export to JSON/CSV
"""

from .signal_engine import SignalEngine

__all__ = ["SignalEngine"]
