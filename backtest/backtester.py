"""
Backtesting engine for forex trading strategies.

This module simulates trading based on generated signals and evaluates
performance using standard metrics.

Execution Model:
1. Signal received at bar close
2. Entry at next bar open (or use entry_price from signal)
3. Exit when SL/TP hit or position closed
4. Single position at a time

Metrics Computed:
- Total PnL
- Win Rate
- Max Drawdown
- Sharpe Ratio
- Number of trades
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt


class Backtester:
    """
    Backtests trading strategies based on signals.

    Attributes:
        initial_capital (float): Starting capital
        position_size (float): Lot size per trade
        commission (float): Commission per trade (as fraction)
        slippage (float): Slippage per trade (as fraction)

    Example:
        >>> backtester = Backtester(
        ...     initial_capital=10000,
        ...     position_size=1.0,
        ...     commission=0.0002,
        ...     slippage=0.0001
        ... )
        >>> results = backtester.run_backtest(df_ohlcv, df_signals)
        >>> metrics = backtester.calculate_metrics()
        >>> backtester.plot_results()
    """

    def __init__(
        self,
        initial_capital: float = 10000.0,
        position_size: float = 1.0,
        commission: float = 0.0002,
        slippage: float = 0.0001,
        output_path: str = "outputs"
    ):
        """
        Initialize the backtester.

        Args:
            initial_capital: Starting capital
            position_size: Lot size or percentage per trade
            commission: Commission as fraction (e.g., 0.0002 = 2 pips)
            slippage: Slippage as fraction (e.g., 0.0001 = 1 pip)
            output_path: Directory for outputs
        """
        self.initial_capital = initial_capital
        self.position_size = position_size
        self.commission = commission
        self.slippage = slippage
        self.output_path = Path(output_path)

        # Results storage
        self.trades = []
        self.equity_curve = []
        self.metrics = {}

        # Create output directory
        self.output_path.mkdir(parents=True, exist_ok=True)

    def run_backtest(
        self,
        df_ohlcv: pd.DataFrame,
        df_signals: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Run backtest simulation.

        Args:
            df_ohlcv: DataFrame with OHLCV data
            df_signals: DataFrame with trading signals

        Returns:
            DataFrame with equity curve and trade history

        Workflow:
            1. Merge OHLCV and signals on timestamp
            2. Iterate through each bar
            3. Execute trades based on signals
            4. Track positions and PnL
            5. Calculate equity curve
        """
        # TODO: Implement backtest logic
        raise NotImplementedError("To be implemented in Phase 4")

    def _execute_trade(
        self,
        signal: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        timestamp: pd.Timestamp,
        current_equity: float
    ) -> Optional[Dict]:
        """
        Execute a single trade.

        Args:
            signal: Trade signal (BUY/SELL/FLAT)
            entry_price: Entry price
            stop_loss: Stop loss level
            take_profit: Take profit level
            timestamp: Trade timestamp
            current_equity: Current equity

        Returns:
            Trade dictionary or None if no trade
        """
        # TODO: Implement trade execution
        raise NotImplementedError("To be implemented in Phase 4")

    def _check_exit(
        self,
        trade: Dict,
        current_bar: pd.Series
    ) -> Tuple[bool, Optional[float], Optional[str]]:
        """
        Check if current position should be exited.

        Checks:
        1. Stop loss hit
        2. Take profit hit
        3. End of bar (if configured)

        Args:
            trade: Current open trade
            current_bar: Current OHLCV bar

        Returns:
            Tuple of (should_exit, exit_price, exit_reason)
        """
        # TODO: Implement exit logic
        raise NotImplementedError("To be implemented in Phase 4")

    def _close_trade(
        self,
        trade: Dict,
        exit_price: float,
        exit_timestamp: pd.Timestamp,
        exit_reason: str
    ) -> Dict:
        """
        Close a trade and calculate PnL.

        Args:
            trade: Open trade
            exit_price: Exit price
            exit_timestamp: Exit timestamp
            exit_reason: Reason for exit (SL/TP/CLOSE)

        Returns:
            Closed trade with PnL
        """
        # TODO: Implement trade closing
        raise NotImplementedError("To be implemented in Phase 4")

    def calculate_metrics(self) -> Dict[str, float]:
        """
        Calculate performance metrics from trades.

        Metrics:
        - total_pnl: Total profit/loss
        - total_return: Total return as percentage
        - win_rate: Percentage of winning trades
        - avg_win: Average winning trade
        - avg_loss: Average losing trade
        - profit_factor: Gross profit / gross loss
        - max_drawdown: Maximum drawdown
        - max_drawdown_pct: Maximum drawdown percentage
        - sharpe_ratio: Risk-adjusted returns
        - num_trades: Total number of trades
        - num_wins: Number of winning trades
        - num_losses: Number of losing trades

        Returns:
            Dictionary of metrics
        """
        # TODO: Implement metrics calculation
        raise NotImplementedError("To be implemented in Phase 4")

    def _calculate_drawdown(self) -> pd.DataFrame:
        """
        Calculate drawdown series from equity curve.

        Returns:
            DataFrame with equity, peak, and drawdown columns
        """
        # TODO: Implement drawdown calculation
        raise NotImplementedError("To be implemented in Phase 4")

    def _calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.0
    ) -> float:
        """
        Calculate Sharpe ratio.

        Sharpe = (mean_return - risk_free_rate) / std_return

        Args:
            returns: Series of returns
            risk_free_rate: Risk-free rate (annualized)

        Returns:
            Sharpe ratio
        """
        # TODO: Implement Sharpe calculation
        raise NotImplementedError("To be implemented in Phase 4")

    def plot_results(
        self,
        save: bool = True,
        show: bool = False
    ) -> None:
        """
        Plot backtest results.

        Creates:
        1. Equity curve
        2. Drawdown chart
        3. Trade distribution

        Args:
            save: Save plots to file
            show: Display plots interactively
        """
        # TODO: Implement plotting
        raise NotImplementedError("To be implemented in Phase 4")

    def _plot_equity_curve(self, ax) -> None:
        """
        Plot equity curve on given axis.

        Args:
            ax: Matplotlib axis
        """
        # TODO: Implement equity curve plotting
        raise NotImplementedError("To be implemented in Phase 4")

    def _plot_drawdown(self, ax) -> None:
        """
        Plot drawdown on given axis.

        Args:
            ax: Matplotlib axis
        """
        # TODO: Implement drawdown plotting
        raise NotImplementedError("To be implemented in Phase 4")

    def export_trades(
        self,
        filename: str = "trade_history.csv"
    ) -> None:
        """
        Export trade history to CSV.

        Args:
            filename: Output filename
        """
        # TODO: Implement trade export
        raise NotImplementedError("To be implemented in Phase 4")

    def print_summary(self) -> None:
        """
        Print a formatted summary of backtest results.

        Displays:
        - Key metrics
        - Trade statistics
        - Performance summary
        """
        # TODO: Implement summary printing
        raise NotImplementedError("To be implemented in Phase 4")
