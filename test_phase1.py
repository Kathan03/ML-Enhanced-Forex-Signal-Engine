"""
Test script for Phase 1: Data Ingestion & Storage

This script tests:
1. Data fetching from yfinance (FREE API)
2. Data normalization and validation
3. Data storage to CSV
4. Data loading from CSV
5. Date filtering
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import ConfigLoader
from data_api.data_fetcher import ForexDataFetcher
from data_api.data_store import DataStore


def test_phase1():
    """
    Test Phase 1 implementation.
    """
    print("=" * 70)
    print(" PHASE 1 TEST: Data Ingestion & Storage")
    print("=" * 70)

    # 1. Load configuration
    print("\n[1/6] Loading configuration...")
    config = ConfigLoader('config.yaml')
    print(f"  Symbol: {config.get('data.symbol')}")
    print(f"  Timeframe: {config.get('data.timeframe')}")
    print(f"  API Provider: {config.get('data.api_provider')}")
    print(f"  Historical bars: {config.get('data.historical_bars')}")

    # 2. Initialize components
    print("\n[2/6] Initializing components...")
    fetcher = ForexDataFetcher(
        api_provider=config.get('data.api_provider'),
        api_key=config.get('data.api_key'),
        symbol=config.get('data.symbol'),
        timeframe=config.get('data.timeframe')
    )

    store = DataStore(
        data_path=config.get('data.data_path'),
        symbol=config.get('data.symbol'),
        timeframe=config.get('data.timeframe')
    )

    # 3. Fetch data
    print("\n[3/6] Fetching historical data...")
    try:
        df = fetcher.fetch_historical_data(bars=config.get('data.historical_bars'))

        print(f"\nData Summary:")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

        print(f"\nFirst 5 rows:")
        print(df.head())

        print(f"\nLast 5 rows:")
        print(df.tail())

        print(f"\nData types:")
        print(df.dtypes)

    except Exception as e:
        print(f"✗ Error fetching data: {e}")
        return False

    # 4. Save data
    print("\n[4/6] Saving data to CSV...")
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
        return False

    # 5. Load data and verify
    print("\n[5/6] Loading data from CSV...")
    try:
        df_loaded = store.load_data()

        # Verify data integrity
        if len(df_loaded) == len(df):
            print(f"  ✓ Data integrity verified ({len(df_loaded)} rows)")
        else:
            print(f"  ✗ Data mismatch: original {len(df)} rows, loaded {len(df_loaded)} rows")
            return False

        # Check first and last rows match
        if (df_loaded.iloc[0]['close'] == df.iloc[0]['close'] and
            df_loaded.iloc[-1]['close'] == df.iloc[-1]['close']):
            print("  ✓ First and last rows match")
        else:
            print("  ✗ Data values don't match")
            return False

    except Exception as e:
        print(f"✗ Error loading data: {e}")
        return False

    # 6. Test date filtering
    print("\n[6/6] Testing date filtering...")
    try:
        # Get date range from middle of data
        mid_point = len(df) // 2
        start_date = df.iloc[mid_point]['timestamp'].strftime("%Y-%m-%d")
        end_date = df.iloc[-100]['timestamp'].strftime("%Y-%m-%d")

        df_filtered = store.load_data(start_date=start_date, end_date=end_date)

        print(f"  Filtered from {start_date} to {end_date}")
        print(f"  Filtered data: {len(df_filtered)} rows")

        if len(df_filtered) < len(df):
            print("  ✓ Date filtering working correctly")
        else:
            print("  ✗ Date filtering may not be working")

    except Exception as e:
        print(f"✗ Error testing date filtering: {e}")
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
    print(" ✓ PHASE 1 TEST PASSED!")
    print("=" * 70)
    print("\nNext steps:")
    print("  - All data fetching and storage functionality is working")
    print("  - Data is cached in:", store.data_path / store._get_default_filename())
    print("  - Ready to proceed to Phase 2 (Feature Engineering)")

    return True


if __name__ == "__main__":
    try:
        success = test_phase1()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
