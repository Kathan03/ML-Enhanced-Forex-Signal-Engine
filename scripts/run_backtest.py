"""
Backtesting script for forex trading strategies.

This script:
1. Loads trained model
2. Loads historical data
3. Generates signals
4. Runs backtest
5. Prints metrics and plots results

Usage:
    python scripts/run_backtest.py --config config.yaml
    python scripts/run_backtest.py --config config.yaml --plot
"""

import argparse
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import ConfigLoader
from data_api.data_store import DataStore
from features.feature_engineering import FeatureEngineer
from model.predict import ModelPredictor
from signals.signal_engine import SignalEngine
from backtest.backtester import Backtester


def main():
    """
    Main backtesting workflow.

    Workflow:
        1. Load configuration
        2. Load trained model
        3. Load historical data
        4. Generate features
        5. Generate predictions
        6. Create signals
        7. Run backtest
        8. Print metrics and plot
    """
    args = parse_args()

    print("=" * 70)
    print(" ML-Enhanced Forex Signal Engine - Backtesting")
    print("=" * 70)

    # 1. Load configuration
    print("\n[1/8] Loading configuration...")
    config = ConfigLoader(args.config)
    print(f"  Config file: {args.config}")

    # 2. Load trained model
    print("\n[2/8] Loading trained model...")
    model_path = args.model
    predictor = ModelPredictor(model_path=model_path)
    predictor.load_model()

    # 3. Load historical data
    print("\n[3/8] Loading historical data...")

    if args.data:
        # Load from specified file
        print(f"  Loading from file: {args.data}")
        store = DataStore(data_path=str(Path(args.data).parent))
        df = store.load_data(filename=Path(args.data).name)
    else:
        # Load from default data path
        store = DataStore(
            data_path=config.get('data.data_path'),
            symbol=config.get('data.symbol'),
            timeframe=config.get('data.timeframe')
        )
        df = store.load_data()

    print(f"  Loaded {len(df)} bars")
    print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

    # 4. Engineer features
    print("\n[4/8] Engineering features...")

    feature_engineer = FeatureEngineer(
        lagged_returns=config.get('features.lagged_returns', [1, 3, 5]),
        rolling_windows=config.get('features.rolling_windows', [10, 20, 50]),
        indicators=config.get('features.indicators', ['sma', 'rsi', 'atr']),
        target_horizon=config.get('features.target_horizon', 1)
    )

    df_features = feature_engineer.create_features(df)
    print(f"  Features created for {len(df_features)} bars")

    # 5. Make predictions
    print("\n[5/8] Making predictions...")

    X = df_features[predictor.feature_names]
    predictions, probabilities = predictor.predict(X)

    df_features['prediction'] = predictions
    df_features['probability'] = probabilities

    valid_predictions = (~pd.isna(probabilities)).sum()
    print(f"  Made {valid_predictions} predictions")

    # 6. Generate signals
    print("\n[6/8] Generating trading signals...")

    signal_engine = SignalEngine(
        buy_threshold=config.get('signals.thresholds.buy_probability', 0.6),
        sell_threshold=config.get('signals.thresholds.sell_probability', 0.4),
        sl_multiplier=config.get('signals.risk_management.stop_loss_atr_multiplier', 2.0),
        tp_multiplier=config.get('signals.risk_management.take_profit_atr_multiplier', 3.0),
        symbol=config.get('data.symbol'),
        output_path=config.get('signals.output_path', 'outputs')
    )

    df_signals = signal_engine.generate_signals(df_features)

    # Get signal statistics
    stats = signal_engine.get_signal_statistics(df_signals)
    print(f"  Total signals: {stats['total_signals']}")
    print(f"  BUY: {stats['buy_count']}, SELL: {stats['sell_count']}, FLAT: {stats['flat_count']}")

    # 7. Run backtest
    print("\n[7/8] Running backtest...")

    backtester = Backtester(
        initial_capital=config.get('backtest.initial_capital', 10000.0),
        position_size=config.get('backtest.position_size', 1.0),
        commission=config.get('backtest.commission', 0.0002),
        slippage=config.get('backtest.slippage', 0.0001),
        output_path=config.get('paths.outputs', 'outputs')
    )

    # Prepare OHLCV data
    df_ohlcv = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

    # Run backtest
    equity_curve = backtester.run_backtest(df_ohlcv, df_signals)

    # 8. Calculate metrics and display results
    print("\n[8/8] Calculating performance metrics...")
    metrics = backtester.calculate_metrics()

    # Print summary
    backtester.print_summary()

    # Export trade history if requested
    if args.save_trades:
        backtester.export_trades(filename="trade_history.csv")

    # Plot results
    if config.get('backtest.plot_equity_curve', True):
        print("\nGenerating plots...")
        backtester.plot_results(save=True, show=args.plot)

    print("\n" + "=" * 70)
    print(" BACKTEST COMPLETE")
    print("=" * 70)
    print(f"\nResults saved to: {backtester.output_path}")
    print("=" * 70)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Backtest forex trading strategy"
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file"
    )

    parser.add_argument(
        "--model",
        type=str,
        default="models/model.joblib",
        help="Path to trained model"
    )

    parser.add_argument(
        "--data",
        type=str,
        help="Path to test data file"
    )

    parser.add_argument(
        "--plot",
        action="store_true",
        help="Display plots"
    )

    parser.add_argument(
        "--save-trades",
        action="store_true",
        help="Save trade history to CSV"
    )

    return parser.parse_args()


if __name__ == "__main__":
    main()
