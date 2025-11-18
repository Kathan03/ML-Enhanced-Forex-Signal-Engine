"""
Test script for Phase 2: Feature Engineering & Model Training

This script tests:
1. Feature engineering (returns, lagged features, indicators)
2. Model training (Logistic Regression and Random Forest)
3. Model evaluation
4. Model saving and loading
5. Making predictions
"""

import sys
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from data_api.data_store import DataStore
from features.feature_engineering import FeatureEngineer
from model.train_model import ModelTrainer
from model.predict import ModelPredictor


def test_phase2():
    """
    Test Phase 2 implementation.
    """
    print("=" * 70)
    print(" PHASE 2 TEST: Feature Engineering & Model Training")
    print("=" * 70)

    # 1. Load data
    print("\n[1/8] Loading data...")

    # Use larger test data file
    test_file = Path("data/raw/test_data_large.csv")
    store = DataStore(data_path="data/raw")

    if not test_file.exists():
        print(f"  Error: Test data not found: {test_file}")
        return False

    df = store.load_data(filename="test_data_large.csv")
    print(f"  Loaded {len(df)} rows")
    print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

    # 2. Test Feature Engineering
    print("\n[2/8] Testing feature engineering...")
    feature_engineer = FeatureEngineer(
        lagged_returns=[1, 3, 5],
        rolling_windows=[10, 20],
        indicators=['sma', 'rsi', 'atr'],
        target_horizon=1
    )

    # Create features
    df_features = feature_engineer.create_features(df)
    print(f"  Features created: {len(df_features.columns)} total columns")
    print(f"  Data rows after feature creation: {len(df_features)}")

    # Create target
    df_with_target = feature_engineer.create_target(df_features)
    print(f"  Target column added")
    print(f"  Data rows after target creation: {len(df_with_target)}")

    # Get feature names
    feature_cols = feature_engineer.get_feature_names()
    print(f"  Feature columns: {len(feature_cols)}")
    print(f"  Sample features: {feature_cols[:5]}")

    # Check for NaN
    nan_count = df_with_target[feature_cols].isna().sum().sum()
    print(f"  NaN values in features: {nan_count}")

    # 3. Test Data Preparation
    print("\n[3/8] Testing data preparation...")
    trainer = ModelTrainer(
        model_type="logistic_regression",
        model_params={"C": 1.0, "max_iter": 1000},
        model_path="models",
        random_state=42
    )

    X_train, X_val, y_train, y_val = trainer.prepare_data(
        df=df_with_target,
        feature_cols=feature_cols,
        target_col='target',
        train_ratio=0.8
    )

    print(f"  Train size: {len(X_train)}, Val size: {len(X_val)}")
    print(f"  Train target distribution: {y_train.value_counts().to_dict()}")
    print(f"  Val target distribution: {y_val.value_counts().to_dict()}")

    # 4. Test Model Training (Logistic Regression)
    print("\n[4/8] Testing Logistic Regression training...")
    metrics_lr = trainer.train(X_train, y_train, X_val, y_val)

    print(f"  Training completed!")
    print(f"  Validation metrics:")
    for metric, value in metrics_lr.items():
        print(f"    {metric}: {value:.4f}")

    # 5. Test Model Saving
    print("\n[5/8] Testing model saving...")
    model_file = "test_lr_model.joblib"
    trainer.save_model(filename=model_file)

    # Verify file exists
    model_path = Path("models") / model_file
    if model_path.exists():
        print(f"  ✓ Model file created: {model_path}")
        print(f"  File size: {model_path.stat().st_size / 1024:.2f} KB")
    else:
        print(f"  ✗ Model file not found: {model_path}")
        return False

    # 6. Test Model Loading
    print("\n[6/8] Testing model loading...")
    predictor = ModelPredictor(model_path=str(model_path))
    predictor.load_model()

    print(f"  ✓ Model loaded successfully")
    print(f"  Model type: {predictor.model_type}")
    print(f"  Features: {len(predictor.feature_names)}")

    # 7. Test Predictions
    print("\n[7/8] Testing predictions...")

    # Predict on validation set
    predictions, probabilities = predictor.predict(X_val)

    print(f"  Predictions shape: {predictions.shape}")
    print(f"  Probabilities shape: {probabilities.shape}")
    print(f"  Sample predictions: {predictions[:5]}")
    print(f"  Sample probabilities: {probabilities[:5]}")

    # Test single prediction
    print("\n  Testing single prediction...")
    sample_features = X_val.iloc[0].to_dict()
    pred, prob = predictor.predict_single(sample_features)
    print(f"    Single prediction: {pred}, probability: {prob:.4f}")

    # 8. Test Random Forest (optional, quick test)
    print("\n[8/8] Testing Random Forest training (quick)...")
    trainer_rf = ModelTrainer(
        model_type="random_forest",
        model_params={"n_estimators": 10, "max_depth": 5},  # Small for speed
        model_path="models",
        random_state=42
    )

    # Use same data
    trainer_rf.feature_names = feature_cols
    metrics_rf = trainer_rf.train(X_train, y_train, X_val, y_val)

    print(f"  Training completed!")
    print(f"  Validation metrics:")
    for metric, value in metrics_rf.items():
        print(f"    {metric}: {value:.4f}")

    # Get feature importance
    print("\n  Feature importance:")
    importance_df = trainer_rf.get_feature_importance()
    if importance_df is not None:
        print(importance_df.head(10).to_string(index=False))

    # Final summary
    print("\n" + "=" * 70)
    print(" ✓ PHASE 2 TEST PASSED!")
    print("=" * 70)
    print("\nSummary:")
    print(f"  Features engineered: {len(feature_cols)}")
    print(f"  Training samples: {len(X_train)}")
    print(f"  Validation samples: {len(X_val)}")
    print(f"\n  Logistic Regression Accuracy: {metrics_lr['accuracy']:.4f}")
    print(f"  Random Forest Accuracy: {metrics_rf['accuracy']:.4f}")
    print("\nNext steps:")
    print("  - Phase 2 is complete (Feature Engineering & Model Training)")
    print("  - Ready to proceed to Phase 3 (Signal Generation)")
    print("  - To train with LSTM, update config.yaml and run scripts/run_train.py")

    return True


if __name__ == "__main__":
    try:
        success = test_phase2()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
