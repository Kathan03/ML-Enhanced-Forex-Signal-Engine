"""
Data storage and caching for forex OHLCV data.

This module handles:
- Saving data to CSV files
- Loading cached data
- Data versioning and updates
- Schema validation
"""

import pandas as pd
from pathlib import Path
from typing import Optional
from datetime import datetime


class DataStore:
    """
    Handles local storage and caching of forex data.

    Attributes:
        data_path (Path): Base directory for data storage
        symbol (str): Forex symbol for file naming
        timeframe (str): Timeframe for file naming

    Example:
        >>> store = DataStore(data_path="data/raw", symbol="EURUSD", timeframe="1h")
        >>> store.save_data(df)
        >>> loaded_df = store.load_data()
    """

    def __init__(
        self,
        data_path: str = "data/raw",
        symbol: str = "EURUSD",
        timeframe: str = "1h"
    ):
        """
        Initialize the data store.

        Args:
            data_path: Directory for data storage
            symbol: Forex pair symbol
            timeframe: Candle timeframe
        """
        self.data_path = Path(data_path)
        self.symbol = symbol
        self.timeframe = timeframe

        # Create directory if it doesn't exist
        self.data_path.mkdir(parents=True, exist_ok=True)

    def save_data(
        self,
        df: pd.DataFrame,
        filename: Optional[str] = None,
        append: bool = False
    ) -> None:
        """
        Save OHLCV data to CSV file.

        Args:
            df: DataFrame with OHLCV data
            filename: Optional custom filename
            append: If True, append to existing data

        Raises:
            ValueError: If data schema is invalid
        """
        # Validate schema
        self._validate_schema(df)

        # Get filepath
        if filename is None:
            filename = self._get_default_filename()

        filepath = self.data_path / filename

        # Handle append mode
        if append and filepath.exists():
            print(f"Appending to existing file: {filepath}")

            # Load existing data
            existing_df = pd.read_csv(filepath)
            existing_df['timestamp'] = pd.to_datetime(existing_df['timestamp'])

            # Combine with new data
            combined_df = pd.concat([existing_df, df], ignore_index=True)

            # Remove duplicates (keep last)
            combined_df = combined_df.drop_duplicates(subset=['timestamp'], keep='last')

            # Sort by timestamp
            combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)

            df = combined_df

        # Save to CSV
        df.to_csv(filepath, index=False)
        print(f"✓ Data saved to: {filepath} ({len(df)} rows)")

    def load_data(
        self,
        filename: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load OHLCV data from CSV file.

        Args:
            filename: Optional custom filename
            start_date: Filter data from this date (YYYY-MM-DD)
            end_date: Filter data to this date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data

        Raises:
            FileNotFoundError: If data file doesn't exist
        """
        # Get filepath
        if filename is None:
            filename = self._get_default_filename()

        filepath = self.data_path / filename

        if not filepath.exists():
            raise FileNotFoundError(
                f"Data file not found: {filepath}\n"
                f"Hint: Fetch data first using ForexDataFetcher"
            )

        # Load CSV
        df = pd.read_csv(filepath)

        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Filter by date range if provided
        if start_date:
            start_dt = pd.to_datetime(start_date)
            df = df[df['timestamp'] >= start_dt]

        if end_date:
            end_dt = pd.to_datetime(end_date)
            df = df[df['timestamp'] <= end_dt]

        # Validate schema
        self._validate_schema(df)

        print(f"✓ Loaded {len(df)} rows from: {filepath}")

        if start_date or end_date:
            print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

        return df

    def data_exists(self, filename: Optional[str] = None) -> bool:
        """
        Check if data file exists.

        Args:
            filename: Optional custom filename

        Returns:
            True if file exists, False otherwise
        """
        if filename is None:
            filename = self._get_default_filename()

        filepath = self.data_path / filename
        return filepath.exists()

    def get_data_info(self, filename: Optional[str] = None) -> dict:
        """
        Get metadata about stored data.

        Args:
            filename: Optional custom filename

        Returns:
            Dictionary with metadata (date range, row count, last updated)
        """
        if filename is None:
            filename = self._get_default_filename()

        filepath = self.data_path / filename

        if not filepath.exists():
            return {
                'exists': False,
                'filename': filename,
                'filepath': str(filepath)
            }

        # Load data to get info
        df = pd.read_csv(filepath)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Get file modification time
        last_modified = datetime.fromtimestamp(filepath.stat().st_mtime)

        info = {
            'exists': True,
            'filename': filename,
            'filepath': str(filepath),
            'rows': len(df),
            'start_date': str(df['timestamp'].min()),
            'end_date': str(df['timestamp'].max()),
            'last_modified': str(last_modified),
            'columns': list(df.columns),
            'file_size_mb': filepath.stat().st_size / (1024 * 1024)
        }

        return info

    def _get_default_filename(self) -> str:
        """
        Generate default filename based on symbol and timeframe.

        Returns:
            Filename string (e.g., "eurusd_1h.csv")
        """
        # Clean symbol (remove special characters like =, /)
        clean_symbol = self.symbol.replace('=', '').replace('/', '').replace('-', '')
        return f"{clean_symbol.lower()}_{self.timeframe}.csv"

    def _validate_schema(self, df: pd.DataFrame) -> bool:
        """
        Validate that DataFrame matches expected schema.

        Required columns: timestamp, open, high, low, close, volume

        Args:
            df: DataFrame to validate

        Returns:
            True if valid

        Raises:
            ValueError: If schema is invalid
        """
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']

        # Check all required columns exist
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(
                f"Missing required columns: {missing_columns}\n"
                f"Expected columns: {required_columns}\n"
                f"Found columns: {list(df.columns)}"
            )

        # Check data types (timestamp should be datetime or convertible)
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            try:
                pd.to_datetime(df['timestamp'])
            except Exception as e:
                raise ValueError(f"'timestamp' column cannot be converted to datetime: {e}")

        # Check numeric columns
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            if not pd.api.types.is_numeric_dtype(df[col]):
                raise ValueError(f"Column '{col}' must be numeric, got {df[col].dtype}")

        return True
