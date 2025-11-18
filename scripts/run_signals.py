"""
Signal generation script for forex ML models.

This script:
1. Loads trained model
2. Loads or fetches forex data
3. Engineers features
4. Makes predictions
5. Generates trading signals
6. Exports signals to JSON/CSV

Usage:
    python scripts/run_signals.py --config config.yaml
    python scripts/run_signals.py --model models/my_model.joblib --output signals_output
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import ConfigLoader
from data_api.data_fetcher import ForexDataFetcher
from data_api.data_store import DataStore
from features.feature_engineering import FeatureEngineer
from model.predict import ModelPredictor
from signals.signal_engine import SignalEngine


def main():
    """
    Main signal generation workflow.

    Workflow:
        1. Load configuration
        2. Load trained model
        3. Load or fetch data
        4. Engineer features
        5. Make predictions
        6. Generate signals
        7. Export signals
    """
    args = parse_args()

    print("=" * 70)
    print(" ML-Enhanced Forex Signal Engine - Signal Generation")
    print("=" * 70)

    # 1. Load configuration
    print("\n[1/7] Loading configuration...")
    config = ConfigLoader(args.config)
    print(f"  Config file: {args.config}")
    print(f"  Symbol: {config.get('data.symbol')}")
    print(f"  Timeframe: {config.get('data.timeframe')}")

    # 2. Load trained model
    print("\n[2/7] Loading trained model...")
    model_path = args.model if args.model else config.get('paths.models', 'models') + '/model.joblib'
    predictor = ModelPredictor(model_path=model_path)
    predictor.load_model()

    # 3. Load or fetch data
    print("\n[3/7] Loading historical data...")

    if args.data:
        # Load from specified file
        print(f"  Loading from file: {args.data}")
        store = DataStore(data_path=str(Path(args.data).parent))
        df = store.load_data(filename=Path(args.data).name)
    else:
        # Use data store to load cached data or fetch new
        store = DataStore(
            data_path=config.get('data.data_path'),
            symbol=config.get('data.symbol'),
            timeframe=config.get('data.timeframe')
        )

        if store.data_exists():
            print("  Loading cached data...")
            df = store.load_data()
        else:
            print("  Fetching fresh data from API...")
            fetcher = ForexDataFetcher(
                api_provider=config.get('data.api_provider'),
                api_key=config.get('data.api_key'),
                symbol=config.get('data.symbol'),
                timeframe=config.get('data.timeframe')
            )
            df = fetcher.fetch_historical_data(bars=config.get('data.historical_bars'))
            store.save_data(df)

    print(f"  Loaded {len(df)} rows")
    print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

    # 4. Engineer features
    print("\n[4/7] Engineering features...")

    feature_engineer = FeatureEngineer(
        lagged_returns=config.get('features.lagged_returns', [1, 3, 5]),
        rolling_windows=config.get('features.rolling_windows', [10, 20, 50]),
        indicators=config.get('features.indicators', ['sma', 'rsi', 'atr']),
        target_horizon=config.get('features.target_horizon', 1)
    )

    # Create features (no target needed for prediction)
    df_features = feature_engineer.create_features(df)

    print(f"  Created features for {len(df_features)} bars")

    # 5. Make predictions
    print("\n[5/7] Making predictions...")

    # Get feature columns
    feature_cols = predictor.feature_names

    # Extract features
    X = df_features[feature_cols]

    # Predict
    predictions, probabilities = predictor.predict(X)

    # Add predictions to dataframe
    df_features['prediction'] = predictions
    df_features['probability'] = probabilities

    # Count valid predictions
    valid_predictions = (~pd.isna(probabilities)).sum()
    print(f"  Made {valid_predictions} predictions")
    print(f"  Average probability: {probabilities[~pd.isna(probabilities)].mean():.4f}")

    # 6. Generate signals
    print("\n[6/7] Generating trading signals...")

    signal_engine = SignalEngine(
        buy_threshold=config.get('signals.thresholds.buy_probability', 0.6),
        sell_threshold=config.get('signals.thresholds.sell_probability', 0.4),
        sl_multiplier=config.get('signals.risk_management.stop_loss_atr_multiplier', 2.0),
        tp_multiplier=config.get('signals.risk_management.take_profit_atr_multiplier', 3.0),
        symbol=config.get('data.symbol'),
        output_path=config.get('signals.output_path', 'outputs')
    )

    signals = signal_engine.generate_signals(df_features)

    # Get statistics
    stats = signal_engine.get_signal_statistics(signals)

    print(f"\nSignal Statistics:")
    print(f"  Total signals: {stats['total_signals']}")
    print(f"  BUY signals: {stats['buy_count']} ({stats['buy_pct']:.1f}%)")
    print(f"  SELL signals: {stats['sell_count']} ({stats['sell_pct']:.1f}%)")
    print(f"  FLAT signals: {stats['flat_count']} ({stats['flat_pct']:.1f}%)")
    print(f"  Average confidence: {stats['avg_confidence']:.4f}")

    # 7. Export signals
    print("\n[7/7] Exporting signals...")

    output_format = args.format if args.format else config.get('signals.output_format', 'both')
    output_name = args.output if args.output else 'signals'

    signal_engine.export_signals(signals, filename=output_name, format=output_format)

    # Optionally filter signals (exclude FLAT)
    if args.filter:
        print("\nFiltering signals (excluding FLAT)...")
        filtered_signals = signal_engine.filter_signals(signals, exclude_flat=True)
        signal_engine.export_signals(filtered_signals, filename=f"{output_name}_filtered", format=output_format)
        print(f"  Filtered signals: {len(filtered_signals)}")

    # Print final summary
    print("\n" + "=" * 70)
    print(" SIGNAL GENERATION COMPLETE")
    print("=" * 70)
    print(f"\nSignals exported to: {signal_engine.output_path}")
    print(f"  Format: {output_format}")
    print(f"  Total signals: {len(signals)}")
    print(f"  Trading signals (BUY/SELL): {stats['buy_count'] + stats['sell_count']}")
    print("=" * 70)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate forex trading signals from ML model"
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
        help="Path to trained model file (overrides config)"
    )

    parser.add_argument(
        "--data",
        type=str,
        help="Path to data file (overrides API fetch)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="signals",
        help="Output filename (without extension)"
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=["csv", "json", "both"],
        help="Output format (overrides config)"
    )

    parser.add_argument(
        "--filter",
        action="store_true",
        help="Export filtered signals (BUY/SELL only) in addition to all signals"
    )

    return parser.parse_args()


if __name__ == "__main__":
    # Import pandas here (needed for predictions)
    import pandas as pd
    main()
