"""
Test script for Phase 3: Signal Generation

This script tests:
1. Loading trained model
2. Feature engineering
3. Making predictions
4. Generating signals (BUY/SELL/FLAT)
5. Applying risk management (SL/TP)
6. Exporting signals (JSON/CSV)
7. Signal statistics
"""

import sys
from pathlib import Path
import pandas as pd
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from data_api.data_store import DataStore
from features.feature_engineering import FeatureEngineer
from model.predict import ModelPredictor
from signals.signal_engine import SignalEngine


def test_phase3():
    """
    Test Phase 3 implementation.
    """
    print("=" * 70)
    print(" PHASE 3 TEST: Signal Generation")
    print("=" * 70)

    # 1. Load data
    print("\n[1/7] Loading data...")

    test_file = Path("data/raw/test_data_large.csv")
    store = DataStore(data_path="data/raw")

    if not test_file.exists():
        print(f"  Error: Test data not found: {test_file}")
        return False

    df = store.load_data(filename="test_data_large.csv")
    print(f"  Loaded {len(df)} rows")

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

    # 3. Engineer features
    print("\n[3/7] Engineering features...")

    feature_engineer = FeatureEngineer(
        lagged_returns=[1, 3, 5],
        rolling_windows=[10, 20],
        indicators=['sma', 'rsi', 'atr'],
        target_horizon=1
    )

    df_features = feature_engineer.create_features(df)
    print(f"  Features created for {len(df_features)} bars")

    # Check if ATR is present
    if 'atr' in df_features.columns:
        print(f"  ✓ ATR available for risk management")
    else:
        print(f"  ⚠ ATR not found, will use default values")

    # 4. Make predictions
    print("\n[4/7] Making predictions...")

    X = df_features[predictor.feature_names]
    predictions, probabilities = predictor.predict(X)

    df_features['prediction'] = predictions
    df_features['probability'] = probabilities

    valid_predictions = (~pd.isna(probabilities)).sum()
    print(f"  Made {valid_predictions} predictions")
    print(f"  Sample probabilities: {probabilities[~pd.isna(probabilities)][:5].tolist()}")

    # 5. Generate signals
    print("\n[5/7] Generating trading signals...")

    signal_engine = SignalEngine(
        buy_threshold=0.6,
        sell_threshold=0.4,
        sl_multiplier=2.0,
        tp_multiplier=3.0,
        symbol="EURUSD",
        output_path="outputs"
    )

    signals = signal_engine.generate_signals(df_features)

    print(f"  Signals shape: {signals.shape}")
    print(f"  Columns: {list(signals.columns)}")

    # Show sample signals
    print(f"\n  Sample signals:")
    print(signals.head(3).to_string(index=False))

    # 6. Test signal statistics
    print("\n[6/7] Computing signal statistics...")

    stats = signal_engine.get_signal_statistics(signals)

    print(f"  Total signals: {stats['total_signals']}")
    print(f"  BUY: {stats['buy_count']} ({stats['buy_pct']:.1f}%)")
    print(f"  SELL: {stats['sell_count']} ({stats['sell_pct']:.1f}%)")
    print(f"  FLAT: {stats['flat_count']} ({stats['flat_pct']:.1f}%)")
    print(f"  Average confidence: {stats['avg_confidence']:.4f}")

    # Validate signal types
    unique_signals = signals['signal'].unique()
    print(f"  Signal types found: {list(unique_signals)}")

    if set(unique_signals).issubset({'BUY', 'SELL', 'FLAT'}):
        print(f"  ✓ All signal types are valid")
    else:
        print(f"  ✗ Invalid signal types detected")
        return False

    # 7. Test signal export
    print("\n[7/7] Testing signal export...")

    # Export to both formats
    signal_engine.export_signals(signals, filename="test_signals", format="both")

    # Verify files exist
    csv_file = Path("outputs/test_signals.csv")
    json_file = Path("outputs/test_signals.json")

    if csv_file.exists():
        print(f"  ✓ CSV file created: {csv_file}")
        print(f"    File size: {csv_file.stat().st_size / 1024:.2f} KB")

        # Verify CSV can be loaded
        df_csv = pd.read_csv(csv_file)
        print(f"    CSV rows: {len(df_csv)}")
    else:
        print(f"  ✗ CSV file not created")
        return False

    if json_file.exists():
        print(f"  ✓ JSON file created: {json_file}")
        print(f"    File size: {json_file.stat().st_size / 1024:.2f} KB")

        # Verify JSON can be loaded
        with open(json_file, 'r') as f:
            signals_json = json.load(f)
        print(f"    JSON entries: {len(signals_json)}")

        # Show sample JSON entry
        if len(signals_json) > 0:
            print(f"\n  Sample JSON signal:")
            print(f"    {json.dumps(signals_json[0], indent=4)}")
    else:
        print(f"  ✗ JSON file not created")
        return False

    # Test filtering
    print("\n  Testing signal filtering...")
    filtered_signals = signal_engine.filter_signals(signals, exclude_flat=True)
    print(f"  Filtered signals (BUY/SELL only): {len(filtered_signals)}")

    buy_sell_count = stats['buy_count'] + stats['sell_count']
    if len(filtered_signals) == buy_sell_count:
        print(f"  ✓ Filtering working correctly")
    else:
        print(f"  ✗ Filtering issue: expected {buy_sell_count}, got {len(filtered_signals)}")

    # Test confidence filtering
    high_confidence_signals = signal_engine.filter_signals(
        signals,
        min_confidence=0.6,
        exclude_flat=True
    )
    print(f"  High confidence signals (≥0.6): {len(high_confidence_signals)}")

    # Validate SL/TP calculations
    print("\n  Validating SL/TP calculations...")

    buy_signals = signals[signals['signal'] == 'BUY']
    if len(buy_signals) > 0:
        sample_buy = buy_signals.iloc[0]
        print(f"  Sample BUY signal:")
        print(f"    Entry: {sample_buy['entry_price']:.5f}")
        print(f"    SL: {sample_buy['stop_loss']:.5f} (below entry: {sample_buy['entry_price'] > sample_buy['stop_loss']})")
        print(f"    TP: {sample_buy['take_profit']:.5f} (above entry: {sample_buy['take_profit'] > sample_buy['entry_price']})")

        if sample_buy['stop_loss'] < sample_buy['entry_price'] < sample_buy['take_profit']:
            print(f"    ✓ BUY SL/TP correctly positioned")
        else:
            print(f"    ✗ BUY SL/TP positioning error")
            return False

    sell_signals = signals[signals['signal'] == 'SELL']
    if len(sell_signals) > 0:
        sample_sell = sell_signals.iloc[0]
        print(f"  Sample SELL signal:")
        print(f"    Entry: {sample_sell['entry_price']:.5f}")
        print(f"    SL: {sample_sell['stop_loss']:.5f} (above entry: {sample_sell['stop_loss'] > sample_sell['entry_price']})")
        print(f"    TP: {sample_sell['take_profit']:.5f} (below entry: {sample_sell['entry_price'] > sample_sell['take_profit']})")

        if sample_sell['take_profit'] < sample_sell['entry_price'] < sample_sell['stop_loss']:
            print(f"    ✓ SELL SL/TP correctly positioned")
        else:
            print(f"    ✗ SELL SL/TP positioning error")
            return False

    # Final summary
    print("\n" + "=" * 70)
    print(" ✓ PHASE 3 TEST PASSED!")
    print("=" * 70)
    print("\nSummary:")
    print(f"  Model loaded: ✓")
    print(f"  Predictions made: {valid_predictions}")
    print(f"  Signals generated: {len(signals)}")
    print(f"  BUY signals: {stats['buy_count']}")
    print(f"  SELL signals: {stats['sell_count']}")
    print(f"  FLAT signals: {stats['flat_count']}")
    print(f"  Files exported: CSV + JSON")
    print(f"\nSignal files:")
    print(f"  {csv_file}")
    print(f"  {json_file}")
    print("\nNext steps:")
    print("  - Phase 3 is complete (Signal Generation)")
    print("  - Ready to proceed to Phase 4 (Backtesting)")
    print("  - Signals are ready for EA integration or backtesting")

    return True


if __name__ == "__main__":
    try:
        success = test_phase3()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
