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
    # TODO: Implement backtesting workflow
    print("Backtesting script - To be implemented in Phase 4")
    print("This will:")
    print("  1. Load trained model")
    print("  2. Load historical test data")
    print("  3. Generate trading signals")
    print("  4. Simulate trades")
    print("  5. Calculate and display metrics")
    print("  6. Plot equity curve and drawdown")


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
    args = parse_args()
    main()
