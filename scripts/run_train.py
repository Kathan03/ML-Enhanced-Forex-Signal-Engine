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
    # TODO: Implement training workflow
    print("Training script - To be implemented in Phase 2")
    print("This will:")
    print("  1. Load configuration from YAML")
    print("  2. Fetch/load historical forex data")
    print("  3. Engineer features")
    print("  4. Train ML model")
    print("  5. Save model and report metrics")


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
        choices=["logistic_regression", "random_forest", "lstm", "kan"],
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
    args = parse_args()
    main()
