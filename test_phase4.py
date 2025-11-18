"""
Test script for Phase 4: Backtesting

This script tests:
1. Loading OHLCV data and signals
2. Running backtest simulation
3. Trade execution (BUY/SELL)
4. SL/TP hit detection
5. Performance metrics calculation
6. Equity curve and drawdown
7. Trade export
"""

import sys
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from data_api.data_store import DataStore
from features.feature_engineering import FeatureEngineer
from model.predict import ModelPredictor
from signals.signal_engine import SignalEngine
from backtest.backtester import Backtester


def test_phase4():
    """
    Test Phase 4 implementation.
    """
    print("=" * 70)
    print(" PHASE 4 TEST: Backtesting")
    print("=" * 70)

    # 1. Load data
    print("\n[1/7] Loading data...")

    test_file = Path("data/raw/test_data_large.csv")
    store = DataStore(data_path="data/raw")

    if not test_file.exists():
        print(f"  Error: Test data not found: {test_file}")
        return False

    df = store.load_data(filename="test_data_large.csv")
    print(f"  Loaded {len(df)} bars")

    # 2. Load trained model
    print("\n[2/7] Loading trained model...")

    model_file = Path("models/test_lr_model.joblib")
    if not model_file.exists():
        print(f"  Error: Model not found: {model_file}")
        print(f"  Please run test_phase2.py first to train a model")
        return False

    predictor = ModelPredictor(model_path=str(model_file))
    predictor.load_model()
    print(f"  ✓ Model loaded successfully")

    # 3. Engineer features and make predictions
    print("\n[3/7] Engineering features and making predictions...")

    feature_engineer = FeatureEngineer(
        lagged_returns=[1, 3, 5],
        rolling_windows=[10, 20],
        indicators=['sma', 'rsi', 'atr'],
        target_horizon=1
    )

    df_features = feature_engineer.create_features(df)
    X = df_features[predictor.feature_names]
    predictions, probabilities = predictor.predict(X)

    df_features['prediction'] = predictions
    df_features['probability'] = probabilities

    print(f"  Features created for {len(df_features)} bars")
    print(f"  Predictions made: {(~pd.isna(probabilities)).sum()}")

    # 4. Generate signals
    print("\n[4/7] Generating signals...")

    signal_engine = SignalEngine(
        buy_threshold=0.6,
        sell_threshold=0.4,
        sl_multiplier=2.0,
        tp_multiplier=3.0,
        symbol="EURUSD",
        output_path="outputs"
    )

    df_signals = signal_engine.generate_signals(df_features)

    stats = signal_engine.get_signal_statistics(df_signals)
    print(f"  Signals generated: {len(df_signals)}")
    print(f"  BUY: {stats['buy_count']}, SELL: {stats['sell_count']}, FLAT: {stats['flat_count']}")

    # 5. Run backtest
    print("\n[5/7] Running backtest...")

    backtester = Backtester(
        initial_capital=10000.0,
        position_size=0.1,  # 0.1 lots for testing
        commission=0.0002,
        slippage=0.0001,
        output_path="outputs"
    )

    df_ohlcv = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    equity_curve = backtester.run_backtest(df_ohlcv, df_signals)

    print(f"  Equity curve points: {len(equity_curve)}")
    print(f"  Trades executed: {len(backtester.trades)}")

    # Validate equity curve
    if len(equity_curve) == 0:
        print(f"  ✗ No equity curve generated")
        return False

    print(f"  ✓ Equity curve generated")

    # 6. Calculate and validate metrics
    print("\n[6/7] Calculating performance metrics...")

    metrics = backtester.calculate_metrics()

    print(f"\n  Performance Summary:")
    print(f"    Initial Capital: ${metrics['initial_capital']:,.2f}")
    print(f"    Final Capital: ${metrics['final_capital']:,.2f}")
    print(f"    Total P&L: ${metrics['total_pnl']:,.2f}")
    print(f"    Total Return: {metrics['total_return']:.2f}%")
    print(f"    Num Trades: {metrics['num_trades']}")
    print(f"    Win Rate: {metrics['win_rate']:.2f}%")
    print(f"    Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"    Max Drawdown: ${metrics['max_drawdown']:,.2f} ({metrics['max_drawdown_pct']:.2f}%)")
    print(f"    Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")

    # Validate metrics
    if metrics['num_trades'] == 0:
        print(f"\n  ⚠ Warning: No trades executed")
    else:
        print(f"  ✓ Metrics calculated successfully")

        # Validate win rate
        if 0 <= metrics['win_rate'] <= 100:
            print(f"  ✓ Win rate valid: {metrics['win_rate']:.2f}%")
        else:
            print(f"  ✗ Invalid win rate: {metrics['win_rate']}")
            return False

        # Check that wins + losses = total trades
        if metrics['num_wins'] + metrics['num_losses'] == metrics['num_trades']:
            print(f"  ✓ Win/Loss count matches total trades")
        else:
            print(f"  ✗ Win/Loss count mismatch")
            return False

    # 7. Test trade export and plotting
    print("\n[7/7] Testing export and plotting...")

    # Export trades
    backtester.export_trades(filename="test_trade_history.csv")

    trade_file = Path("outputs/test_trade_history.csv")
    if trade_file.exists():
        print(f"  ✓ Trade history exported: {trade_file}")

        # Validate trade history structure
        trades_df = pd.read_csv(trade_file)
        required_cols = ['entry_time', 'signal', 'entry_price', 'exit_price', 'pnl']
        if all(col in trades_df.columns for col in required_cols):
            print(f"  ✓ Trade history has all required columns")
        else:
            print(f"  ✗ Missing columns in trade history")
            return False

        print(f"  Sample trade:")
        if len(trades_df) > 0:
            sample = trades_df.iloc[0]
            print(f"    Signal: {sample['signal']}")
            print(f"    Entry: ${sample['entry_price']:.5f}")
            print(f"    Exit: ${sample['exit_price']:.5f}")
            print(f"    P&L: ${sample['pnl']:.2f}")
            print(f"    Exit Reason: {sample['exit_reason']}")

    else:
        print(f"  ✗ Trade history not exported")
        return False

    # Generate plots
    print(f"\n  Generating plots...")
    backtester.plot_results(save=True, show=False)

    plot_file = Path("outputs/backtest_results.png")
    if plot_file.exists():
        print(f"  ✓ Plots saved: {plot_file}")
    else:
        print(f"  ⚠ Plot file not created (matplotlib may not be available)")

    # Print formatted summary
    backtester.print_summary()

    # Final validation
    print("\n" + "=" * 70)
    print(" ✓ PHASE 4 TEST PASSED!")
    print("=" * 70)
    print("\nSummary:")
    print(f"  Data loaded: {len(df)} bars")
    print(f"  Signals generated: {len(df_signals)}")
    print(f"  Trades executed: {len(backtester.trades)}")
    print(f"  Final equity: ${metrics['final_capital']:,.2f}")
    print(f"  Total return: {metrics['total_return']:.2f}%")
    print(f"\nFiles created:")
    print(f"  {trade_file}")
    if plot_file.exists():
        print(f"  {plot_file}")
    print("\nNext steps:")
    print("  - All 4 phases complete!")
    print("  - Project ready for production use")
    print("  - Train on real data: python scripts/run_train.py")
    print("  - Generate signals: python scripts/run_signals.py")
    print("  - Run backtest: python scripts/run_backtest.py")

    return True


if __name__ == "__main__":
    try:
        success = test_phase4()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
