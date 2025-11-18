"""
Training script for forex ML models.

This script:
1. Loads historical forex data
2. Engineers features
3. Trains ML model
4. Saves model to disk
5. Prints training metrics

Usage:
    python scripts/run_train.py --config config.yaml
    python scripts/run_train.py --config config.yaml --model random_forest
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
from model.train_model import ModelTrainer


def main():
    """
    Main training workflow.

    Workflow:
        1. Load configuration
        2. Load or fetch data
        3. Engineer features
        4. Split data
        5. Train model
        6. Evaluate and save
    """
    args = parse_args()

    print("=" * 70)
    print(" ML-Enhanced Forex Signal Engine - Model Training")
    print("=" * 70)

    # 1. Load configuration
    print("\n[1/6] Loading configuration...")
    config = ConfigLoader(args.config)
    print(f"  Config file: {args.config}")
    print(f"  Symbol: {config.get('data.symbol')}")
    print(f"  Timeframe: {config.get('data.timeframe')}")

    # Override model type if specified
    model_type = args.model if args.model else config.get('model.type', 'logistic_regression')
    print(f"  Model type: {model_type}")

    # 2. Load or fetch data
    print("\n[2/6] Loading historical data...")

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

    # 3. Engineer features
    print("\n[3/6] Engineering features...")

    feature_engineer = FeatureEngineer(
        lagged_returns=config.get('features.lagged_returns', [1, 3, 5]),
        rolling_windows=config.get('features.rolling_windows', [10, 20, 50]),
        indicators=config.get('features.indicators', ['sma', 'rsi', 'atr']),
        target_horizon=config.get('features.target_horizon', 1)
    )

    # Create features and target
    df_features = feature_engineer.create_features(df)
    df_with_target = feature_engineer.create_target(df_features)

    # Get feature names (exclude OHLCV, timestamp, target)
    feature_cols = feature_engineer.get_feature_names(df_with_target)

    print(f"  Created {len(feature_cols)} features")
    print(f"  Sample features: {feature_cols[:5]}")

    # 4. Prepare data (time-based split)
    print("\n[4/6] Preparing train/validation split...")

    trainer = ModelTrainer(
        model_type=model_type,
        model_params=config.get('model.params', {}),
        model_path=config.get('model.model_path', 'models'),
        random_state=config.get('model.random_state', 42)
    )

    X_train, X_val, y_train, y_val = trainer.prepare_data(
        df=df_with_target,
        feature_cols=feature_cols,
        target_col='target',
        train_ratio=config.get('model.train_ratio', 0.8)
    )

    # 5. Train model
    print("\n[5/6] Training model...")
    metrics = trainer.train(X_train, y_train, X_val, y_val)

    # 6. Save model and report
    print("\n[6/6] Saving model...")
    trainer.save_model(filename=Path(args.output).name)

    # Print final metrics
    print("\n" + "=" * 70)
    print(" TRAINING COMPLETE")
    print("=" * 70)
    print(f"\nFinal Metrics:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")

    # Print feature importance (if available)
    importance_df = trainer.get_feature_importance()
    if importance_df is not None:
        print(f"\nTop 10 Most Important Features:")
        print(importance_df.head(10).to_string(index=False))

    print(f"\nModel saved to: {args.output}")
    print("Training successful!")
    print("=" * 70)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Train forex ML model"
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
        choices=["logistic_regression", "random_forest", "lstm"],
        help="Model type (overrides config)"
    )

    parser.add_argument(
        "--data",
        type=str,
        help="Path to data file (overrides API fetch)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="models/model.joblib",
        help="Output path for saved model"
    )

    return parser.parse_args()


if __name__ == "__main__":
    main()
