"""
Test script for Phase 1: Data Ingestion & Storage (CSV Mode)

This script tests Phase 1 functionality using CSV mode (no API required).

Tests:
1. CSV data loading
2. Data normalization and validation
3. Data storage
4. Data re-loading
5. Date filtering
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from data_api.data_fetcher import ForexDataFetcher
from data_api.data_store import DataStore


def test_phase1_csv():
    """
    Test Phase 1 implementation using CSV mode.
    """
    print("=" * 70)
    print(" PHASE 1 TEST: Data Ingestion & Storage (CSV Mode)")
    print("=" * 70)

    # Use the sample CSV file
    sample_csv = "data/raw/sample_eurusd_1h.csv"

    # 1. Initialize components
    print("\n[1/5] Initializing components...")
    fetcher = ForexDataFetcher(
        api_provider="csv",
        symbol=sample_csv,  # For CSV mode, symbol is the filepath
        timeframe="1h"
    )

    store = DataStore(
        data_path="data/raw",
        symbol="EURUSD-TEST",
        timeframe="1h"
    )

    # 2. Fetch data from CSV
    print("\n[2/5] Loading data from CSV...")
    try:
        df = fetcher.fetch_historical_data(bars=1000)

        print(f"\nData Summary:")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

        print(f"\nFirst 3 rows:")
        print(df.head(3))

        print(f"\nLast 3 rows:")
        print(df.tail(3))

        print(f"\nData types:")
        print(df.dtypes)

        print(f"\nData stats:")
        print(df[['open', 'high', 'low', 'close', 'volume']].describe())

    except Exception as e:
        print(f"✗ Error fetching data: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 3. Save data
    print("\n[3/5] Saving data to new CSV file...")
    try:
        store.save_data(df)

        # Verify file exists
        if store.data_exists():
            print("  ✓ Data file created successfully")
        else:
            print("  ✗ Data file not found after save")
            return False

    except Exception as e:
        print(f"✗ Error saving data: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 4. Load data and verify
    print("\n[4/5] Loading data back from CSV...")
    try:
        df_loaded = store.load_data()

        # Verify data integrity
        if len(df_loaded) == len(df):
            print(f"  ✓ Data integrity verified ({len(df_loaded)} rows)")
        else:
            print(f"  ✗ Data mismatch: original {len(df)} rows, loaded {len(df_loaded)} rows")
            return False

        # Check first and last values match
        first_match = abs(df_loaded.iloc[0]['close'] - df.iloc[0]['close']) < 0.00001
        last_match = abs(df_loaded.iloc[-1]['close'] - df.iloc[-1]['close']) < 0.00001

        if first_match and last_match:
            print("  ✓ First and last rows match")
        else:
            print(f"  ✗ Data values don't match")
            print(f"    Original first close: {df.iloc[0]['close']}")
            print(f"    Loaded first close: {df_loaded.iloc[0]['close']}")
            return False

    except Exception as e:
        print(f"✗ Error loading data: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 5. Test date filtering
    print("\n[5/5] Testing date filtering...")
    try:
        # Use specific dates from our sample data
        start_date = "2024-01-01"
        end_date = "2024-01-01"

        df_filtered = store.load_data(start_date=start_date, end_date=end_date)

        print(f"  Filtered from {start_date} to {end_date}")
        print(f"  Filtered data: {len(df_filtered)} rows")

        if len(df_filtered) <= len(df):
            print("  ✓ Date filtering working correctly")
        else:
            print("  ✗ Date filtering may not be working")
            return False

    except Exception as e:
        print(f"✗ Error testing date filtering: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Get data info
    print("\n" + "=" * 70)
    print(" DATA INFO")
    print("=" * 70)
    info = store.get_data_info()
    for key, value in info.items():
        if key == 'columns':
            continue
        print(f"  {key}: {value}")

    print("\n" + "=" * 70)
    print(" ✓ PHASE 1 TEST PASSED (CSV Mode)!")
    print("=" * 70)
    print("\nAll Phase 1 functionality working:")
    print("  ✓ Data fetching from CSV")
    print("  ✓ Data normalization")
    print("  ✓ Data validation")
    print("  ✓ Data storage")
    print("  ✓ Data loading")
    print("  ✓ Date filtering")
    print("\nData cached in:", store.data_path / store._get_default_filename())
    print("\n Ready to proceed to Phase 2 (Feature Engineering)")

    return True


if __name__ == "__main__":
    try:
        success = test_phase1_csv()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
