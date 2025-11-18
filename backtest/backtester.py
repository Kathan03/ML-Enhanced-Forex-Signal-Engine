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
        print(f"Running backtest on {len(df_signals)} signals...")

        # Merge OHLCV and signals
        df = pd.merge(df_ohlcv, df_signals, on='timestamp', how='left')
        df = df.sort_values('timestamp').reset_index(drop=True)

        # Initialize tracking variables
        current_equity = self.initial_capital
        current_trade = None
        equity_history = []

        # Iterate through each bar
        for idx, row in df.iterrows():
            # Check if we have an open trade
            if current_trade is not None:
                # Check for exit conditions
                should_exit, exit_price, exit_reason = self._check_exit(current_trade, row)

                if should_exit:
                    # Close the trade
                    closed_trade = self._close_trade(
                        current_trade,
                        exit_price,
                        row['timestamp'],
                        exit_reason
                    )
                    self.trades.append(closed_trade)

                    # Update equity
                    current_equity += closed_trade['pnl']
                    current_trade = None

            # Check for new signal (only if no open trade)
            if current_trade is None and pd.notna(row.get('signal')):
                signal = row['signal']

                # Only trade on BUY/SELL signals
                if signal in ['BUY', 'SELL']:
                    current_trade = self._execute_trade(
                        signal=signal,
                        entry_price=row.get('entry_price', row['close']),
                        stop_loss=row.get('stop_loss'),
                        take_profit=row.get('take_profit'),
                        timestamp=row['timestamp'],
                        current_equity=current_equity
                    )

            # Record equity
            equity_history.append({
                'timestamp': row['timestamp'],
                'equity': current_equity,
                'in_trade': current_trade is not None
            })

        # Close any remaining open trade at the last bar
        if current_trade is not None:
            last_row = df.iloc[-1]
            closed_trade = self._close_trade(
                current_trade,
                last_row['close'],
                last_row['timestamp'],
                'END'
            )
            self.trades.append(closed_trade)
            current_equity += closed_trade['pnl']

        # Store equity curve
        self.equity_curve = pd.DataFrame(equity_history)

        print(f"✓ Backtest complete: {len(self.trades)} trades executed")

        return self.equity_curve

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
        if signal not in ['BUY', 'SELL']:
            return None

        # Apply slippage
        if signal == 'BUY':
            actual_entry = entry_price * (1 + self.slippage)
        else:  # SELL
            actual_entry = entry_price * (1 - self.slippage)

        # Calculate position size in units
        # For forex, 1 lot = 100,000 units
        position_value = self.position_size * 100000

        # Create trade record
        trade = {
            'entry_time': timestamp,
            'signal': signal,
            'entry_price': actual_entry,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'position_size': self.position_size,
            'position_value': position_value,
            'equity_at_entry': current_equity
        }

        return trade

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
        signal = trade['signal']
        stop_loss = trade['stop_loss']
        take_profit = trade['take_profit']

        # For BUY positions
        if signal == 'BUY':
            # Check if stop loss hit (low touched SL)
            if stop_loss is not None and current_bar['low'] <= stop_loss:
                return True, stop_loss, 'SL'

            # Check if take profit hit (high touched TP)
            if take_profit is not None and current_bar['high'] >= take_profit:
                return True, take_profit, 'TP'

        # For SELL positions
        elif signal == 'SELL':
            # Check if stop loss hit (high touched SL)
            if stop_loss is not None and current_bar['high'] >= stop_loss:
                return True, stop_loss, 'SL'

            # Check if take profit hit (low touched TP)
            if take_profit is not None and current_bar['low'] <= take_profit:
                return True, take_profit, 'TP'

        # No exit condition met
        return False, None, None

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
        signal = trade['signal']
        entry_price = trade['entry_price']
        position_value = trade['position_value']

        # Calculate price change
        if signal == 'BUY':
            price_change = exit_price - entry_price
        else:  # SELL
            price_change = entry_price - exit_price

        # Calculate gross PnL (price change * position size)
        gross_pnl = price_change * position_value

        # Apply commission (on entry and exit)
        commission_cost = entry_price * position_value * self.commission * 2  # Entry + Exit

        # Net PnL
        net_pnl = gross_pnl - commission_cost

        # Add exit information to trade
        trade['exit_time'] = exit_timestamp
        trade['exit_price'] = exit_price
        trade['exit_reason'] = exit_reason
        trade['gross_pnl'] = gross_pnl
        trade['commission'] = commission_cost
        trade['pnl'] = net_pnl
        trade['return_pct'] = (net_pnl / trade['equity_at_entry']) * 100

        return trade

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
        if len(self.trades) == 0:
            return {
                'total_pnl': 0.0,
                'total_return': 0.0,
                'win_rate': 0.0,
                'num_trades': 0,
                'num_wins': 0,
                'num_losses': 0
            }

        trades_df = pd.DataFrame(self.trades)

        # Basic metrics
        total_pnl = trades_df['pnl'].sum()
        total_return = (total_pnl / self.initial_capital) * 100

        # Win/Loss metrics
        wins = trades_df[trades_df['pnl'] > 0]
        losses = trades_df[trades_df['pnl'] <= 0]

        num_trades = len(trades_df)
        num_wins = len(wins)
        num_losses = len(losses)
        win_rate = (num_wins / num_trades * 100) if num_trades > 0 else 0

        avg_win = wins['pnl'].mean() if len(wins) > 0 else 0
        avg_loss = losses['pnl'].mean() if len(losses) > 0 else 0

        # Profit factor
        gross_profit = wins['pnl'].sum() if len(wins) > 0 else 0
        gross_loss = abs(losses['pnl'].sum()) if len(losses) > 0 else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0

        # Drawdown metrics
        dd_df = self._calculate_drawdown()
        max_drawdown = dd_df['drawdown'].min() if len(dd_df) > 0 else 0
        max_drawdown_pct = dd_df['drawdown_pct'].min() if len(dd_df) > 0 else 0

        # Sharpe ratio
        returns = trades_df['return_pct']
        sharpe_ratio = self._calculate_sharpe_ratio(returns)

        # Average trade duration (in bars)
        avg_duration = (trades_df['exit_time'] - trades_df['entry_time']).mean()

        self.metrics = {
            'initial_capital': self.initial_capital,
            'final_capital': self.initial_capital + total_pnl,
            'total_pnl': total_pnl,
            'total_return': total_return,
            'num_trades': num_trades,
            'num_wins': num_wins,
            'num_losses': num_losses,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'sharpe_ratio': sharpe_ratio,
            'avg_trade_duration': str(avg_duration)
        }

        return self.metrics

    def _calculate_drawdown(self) -> pd.DataFrame:
        """
        Calculate drawdown series from equity curve.

        Returns:
            DataFrame with equity, peak, and drawdown columns
        """
        if len(self.equity_curve) == 0:
            return pd.DataFrame()

        equity = self.equity_curve['equity'].values
        peak = np.maximum.accumulate(equity)
        drawdown = equity - peak
        drawdown_pct = (drawdown / peak) * 100

        dd_df = pd.DataFrame({
            'equity': equity,
            'peak': peak,
            'drawdown': drawdown,
            'drawdown_pct': drawdown_pct
        })

        return dd_df

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
        if len(returns) == 0 or returns.std() == 0:
            return 0.0

        mean_return = returns.mean()
        std_return = returns.std()

        sharpe = (mean_return - risk_free_rate) / std_return

        return sharpe

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
        if len(self.equity_curve) == 0:
            print("No equity curve data to plot")
            return

        fig, axes = plt.subplots(2, 1, figsize=(12, 8))

        # Plot equity curve
        self._plot_equity_curve(axes[0])

        # Plot drawdown
        self._plot_drawdown(axes[1])

        plt.tight_layout()

        if save:
            output_file = self.output_path / "backtest_results.png"
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            print(f"  ✓ Plot saved to: {output_file}")

        if show:
            plt.show()
        else:
            plt.close()

    def _plot_equity_curve(self, ax) -> None:
        """
        Plot equity curve on given axis.

        Args:
            ax: Matplotlib axis
        """
        equity = self.equity_curve['equity']
        timestamps = self.equity_curve['timestamp']

        ax.plot(timestamps, equity, label='Equity', color='blue', linewidth=1.5)
        ax.axhline(y=self.initial_capital, color='gray', linestyle='--', alpha=0.5, label='Initial Capital')

        ax.set_title('Equity Curve', fontsize=12, fontweight='bold')
        ax.set_xlabel('Time')
        ax.set_ylabel('Equity ($)')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)

    def _plot_drawdown(self, ax) -> None:
        """
        Plot drawdown on given axis.

        Args:
            ax: Matplotlib axis
        """
        dd_df = self._calculate_drawdown()
        if len(dd_df) == 0:
            return

        timestamps = self.equity_curve['timestamp']
        drawdown_pct = dd_df['drawdown_pct']

        ax.fill_between(timestamps, drawdown_pct, 0, color='red', alpha=0.3, label='Drawdown')
        ax.plot(timestamps, drawdown_pct, color='red', linewidth=1)

        ax.set_title('Drawdown', fontsize=12, fontweight='bold')
        ax.set_xlabel('Time')
        ax.set_ylabel('Drawdown (%)')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)

    def export_trades(
        self,
        filename: str = "trade_history.csv"
    ) -> None:
        """
        Export trade history to CSV.

        Args:
            filename: Output filename
        """
        if len(self.trades) == 0:
            print("No trades to export")
            return

        trades_df = pd.DataFrame(self.trades)
        filepath = self.output_path / filename
        trades_df.to_csv(filepath, index=False)

        print(f"  ✓ Trade history exported to: {filepath}")

    def print_summary(self) -> None:
        """
        Print a formatted summary of backtest results.

        Displays:
        - Key metrics
        - Trade statistics
        - Performance summary
        """
        if len(self.metrics) == 0:
            print("No metrics available. Run calculate_metrics() first.")
            return

        print("\n" + "=" * 70)
        print(" BACKTEST RESULTS SUMMARY")
        print("=" * 70)

        print("\n📊 Performance Metrics:")
        print(f"  Initial Capital:    ${self.metrics['initial_capital']:,.2f}")
        print(f"  Final Capital:      ${self.metrics['final_capital']:,.2f}")
        print(f"  Total P&L:          ${self.metrics['total_pnl']:,.2f}")
        print(f"  Total Return:       {self.metrics['total_return']:.2f}%")

        print("\n📈 Trade Statistics:")
        print(f"  Total Trades:       {self.metrics['num_trades']}")
        print(f"  Winning Trades:     {self.metrics['num_wins']}")
        print(f"  Losing Trades:      {self.metrics['num_losses']}")
        print(f"  Win Rate:           {self.metrics['win_rate']:.2f}%")

        print("\n💰 Profit Analysis:")
        print(f"  Gross Profit:       ${self.metrics['gross_profit']:,.2f}")
        print(f"  Gross Loss:         ${self.metrics['gross_loss']:,.2f}")
        print(f"  Profit Factor:      {self.metrics['profit_factor']:.2f}")
        print(f"  Average Win:        ${self.metrics['avg_win']:,.2f}")
        print(f"  Average Loss:       ${self.metrics['avg_loss']:,.2f}")

        print("\n📉 Risk Metrics:")
        print(f"  Max Drawdown:       ${self.metrics['max_drawdown']:,.2f}")
        print(f"  Max Drawdown %:     {self.metrics['max_drawdown_pct']:.2f}%")
        print(f"  Sharpe Ratio:       {self.metrics['sharpe_ratio']:.2f}")

        print("\n⏱️  Trade Duration:")
        print(f"  Avg Duration:       {self.metrics['avg_trade_duration']}")

        print("\n" + "=" * 70)
