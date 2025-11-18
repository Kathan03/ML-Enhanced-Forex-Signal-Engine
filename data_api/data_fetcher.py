"""
Data fetcher for forex OHLCV data from various API providers.

This module handles:
- API authentication and rate limiting
- Data fetching from multiple providers (yfinance, Twelve Data, Alpha Vantage, etc.)
- Data validation and normalization
- Error handling and retries

Supported providers:
- yfinance (Yahoo Finance) - FREE, no API key needed!
- Twelve Data API - Free tier available
- Alpha Vantage API - Free tier available
- CSV file loading (for offline testing)
"""

import pandas as pd
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import time
from pathlib import Path


class ForexDataFetcher:
    """
    Fetches forex OHLCV data from various API providers.

    Attributes:
        api_provider (str): Name of the API provider (yfinance, twelve_data, alpha_vantage, csv)
        api_key (str): API key for authentication
        symbol (str): Forex symbol (e.g., "EURUSD=X" for yfinance, "EURUSD" for others)
        timeframe (str): Timeframe for candles (e.g., "1h", "15m")

    Example:
        >>> # Using yfinance (FREE!)
        >>> fetcher = ForexDataFetcher(
        ...     api_provider="yfinance",
        ...     symbol="EURUSD=X",
        ...     timeframe="1h"
        ... )
        >>> df = fetcher.fetch_historical_data(bars=1000)
    """

    def __init__(
        self,
        api_provider: str = "yfinance",
        api_key: Optional[str] = None,
        symbol: str = "EURUSD=X",
        timeframe: str = "1h"
    ):
        """
        Initialize the forex data fetcher.

        Args:
            api_provider: API provider name
            api_key: API authentication key (not needed for yfinance)
            symbol: Forex pair symbol
            timeframe: Candle timeframe
        """
        self.api_provider = api_provider.lower()
        self.api_key = api_key
        self.symbol = symbol
        self.timeframe = timeframe

        # API endpoints
        self.endpoints = {
            "twelve_data": "https://api.twelvedata.com/time_series",
            "alpha_vantage": "https://www.alphavantage.co/query"
        }

    def fetch_historical_data(
        self,
        bars: int = 1000,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data.

        Args:
            bars: Number of bars to fetch
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume

        Raises:
            ValueError: If API provider is not supported
            requests.RequestException: If API request fails
        """
        print(f"Fetching {bars} bars from {self.api_provider}...")

        if self.api_provider == "yfinance":
            df = self._fetch_from_yfinance(bars, start_date, end_date)
        elif self.api_provider == "twelve_data":
            df = self._fetch_from_twelve_data(bars, start_date, end_date)
        elif self.api_provider == "alpha_vantage":
            df = self._fetch_from_alpha_vantage(bars, start_date, end_date)
        elif self.api_provider == "csv":
            df = self._fetch_from_csv(bars, start_date, end_date)
        else:
            raise ValueError(
                f"Unsupported API provider: {self.api_provider}. "
                f"Supported: yfinance, twelve_data, alpha_vantage, csv"
            )

        # Normalize and validate
        df = self._normalize_data(df)
        self._validate_data(df)

        print(f"Successfully fetched {len(df)} bars")
        return df

    def fetch_realtime_data(self, bars: int = 100) -> pd.DataFrame:
        """
        Fetch the most recent N bars for live/simulation mode.

        Args:
            bars: Number of recent bars to fetch

        Returns:
            DataFrame with recent OHLCV data
        """
        # For realtime, we just fetch recent data
        # Set end_date to today
        end_date = datetime.now().strftime("%Y-%m-%d")

        return self.fetch_historical_data(bars=bars, end_date=end_date)

    def _fetch_from_yfinance(
        self,
        bars: int,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> pd.DataFrame:
        """
        Fetch data from Yahoo Finance using yfinance (FREE!).

        Args:
            bars: Number of bars
            start_date: Start date
            end_date: End date

        Returns:
            Raw DataFrame from yfinance
        """
        try:
            import yfinance as yf
        except ImportError:
            raise ImportError(
                "yfinance is not installed. Install it with: pip install yfinance"
            )

        # Map timeframe to yfinance interval
        interval_map = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "1h": "1h",
            "4h": "4h",
            "1d": "1d"
        }
        interval = interval_map.get(self.timeframe, "1h")

        # Calculate date range if not provided
        if not end_date:
            end_date = datetime.now()
        else:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        if not start_date:
            # Calculate start date based on bars
            # Rough estimation: 1 bar per period
            if interval == "1h":
                days_back = bars // 24 + 30  # Add buffer
            elif interval == "1d":
                days_back = bars + 30
            elif interval == "15m":
                days_back = bars // 96 + 30
            else:
                days_back = 60  # Default 2 months

            start_date = end_date - timedelta(days=days_back)
        else:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")

        # Fetch data
        ticker = yf.Ticker(self.symbol)
        df = ticker.history(
            start=start_date,
            end=end_date,
            interval=interval
        )

        if df.empty:
            raise ValueError(
                f"No data returned from yfinance for {self.symbol}. "
                f"Check symbol format (e.g., 'EURUSD=X' for forex)"
            )

        # Limit to requested bars
        if len(df) > bars:
            df = df.iloc[-bars:]

        return df

    def _fetch_from_twelve_data(
        self,
        bars: int,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> pd.DataFrame:
        """
        Fetch data from Twelve Data API.

        Args:
            bars: Number of bars
            start_date: Start date
            end_date: End date

        Returns:
            Raw DataFrame from API
        """
        if not self.api_key:
            raise ValueError("API key required for Twelve Data")

        # Map timeframe
        interval_map = {
            "1m": "1min",
            "5m": "5min",
            "15m": "15min",
            "1h": "1h",
            "4h": "4h",
            "1d": "1day"
        }
        interval = interval_map.get(self.timeframe, "1h")

        # Build request parameters
        params = {
            "symbol": self.symbol,
            "interval": interval,
            "apikey": self.api_key,
            "outputsize": min(bars, 5000),  # Max 5000
            "format": "JSON"
        }

        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        # Make request with retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    self.endpoints["twelve_data"],
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()

                if "values" not in data:
                    if "code" in data and data["code"] == 429:
                        raise ValueError("Rate limit exceeded. Please wait and try again.")
                    raise ValueError(f"API error: {data.get('message', 'Unknown error')}")

                # Convert to DataFrame
                df = pd.DataFrame(data["values"])
                return df

            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Request failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Failed to fetch from Twelve Data: {str(e)}")

    def _fetch_from_alpha_vantage(
        self,
        bars: int,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> pd.DataFrame:
        """
        Fetch data from Alpha Vantage API.

        Args:
            bars: Number of bars
            start_date: Start date
            end_date: End date

        Returns:
            Raw DataFrame from API
        """
        if not self.api_key:
            raise ValueError("API key required for Alpha Vantage")

        # Parse symbol (e.g., "EURUSD" -> from_currency="EUR", to_currency="USD")
        if len(self.symbol) == 6:
            from_currency = self.symbol[:3]
            to_currency = self.symbol[3:6]
        else:
            raise ValueError(f"Invalid symbol format for Alpha Vantage: {self.symbol}")

        # Map timeframe
        if self.timeframe in ["1m", "5m", "15m", "1h"]:
            function = "FX_INTRADAY"
            interval_map = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "60min"}
            interval = interval_map.get(self.timeframe, "60min")
        else:
            function = "FX_DAILY"
            interval = None

        # Build parameters
        params = {
            "function": function,
            "from_symbol": from_currency,
            "to_symbol": to_currency,
            "apikey": self.api_key,
            "outputsize": "full" if bars > 100 else "compact"
        }

        if interval:
            params["interval"] = interval

        # Make request
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    self.endpoints["alpha_vantage"],
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()

                # Get time series data
                if function == "FX_INTRADAY":
                    key = f"Time Series FX ({interval})"
                else:
                    key = "Time Series FX (Daily)"

                if key not in data:
                    raise ValueError(f"API error: {data.get('Note', data.get('Error Message', 'Unknown error'))}")

                # Convert to DataFrame
                df = pd.DataFrame.from_dict(data[key], orient='index')
                return df

            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Request failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Failed to fetch from Alpha Vantage: {str(e)}")

    def _fetch_from_csv(
        self,
        bars: int,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> pd.DataFrame:
        """
        Load data from CSV file.

        Args:
            bars: Number of bars
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame from CSV
        """
        # Assume symbol is the file path
        filepath = Path(self.symbol)

        if not filepath.exists():
            raise FileNotFoundError(f"CSV file not found: {filepath}")

        df = pd.read_csv(filepath)

        # Filter by date if provided
        if 'timestamp' in df.columns or 'date' in df.columns:
            date_col = 'timestamp' if 'timestamp' in df.columns else 'date'
            df[date_col] = pd.to_datetime(df[date_col])

            if start_date:
                df = df[df[date_col] >= start_date]
            if end_date:
                df = df[df[date_col] <= end_date]

        # Limit to requested bars
        if len(df) > bars:
            df = df.iloc[-bars:]

        return df

    def _normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize data to standard schema.

        Converts various API formats to standard schema:
        - timestamp: datetime
        - open: float
        - high: float
        - low: float
        - close: float
        - volume: float

        Args:
            df: Raw DataFrame from API

        Returns:
            Normalized DataFrame
        """
        df = df.copy()

        # Handle different column naming conventions
        column_map = {}

        # yfinance format (already good, but index is datetime)
        if "Open" in df.columns:
            column_map = {
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume"
            }
            # Index is the timestamp
            df = df.reset_index()
            if "Date" in df.columns:
                column_map["Date"] = "timestamp"
            elif "Datetime" in df.columns:
                column_map["Datetime"] = "timestamp"

        # Twelve Data format
        elif "datetime" in df.columns:
            column_map = {
                "datetime": "timestamp",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume"
            }

        # Alpha Vantage format
        elif "1. open" in df.columns:
            column_map = {
                "1. open": "open",
                "2. high": "high",
                "3. low": "low",
                "4. close": "close",
                "5. volume": "volume"
            }
            df = df.reset_index()
            df = df.rename(columns={"index": "timestamp"})

        # Rename columns
        df = df.rename(columns=column_map)

        # Ensure we have required columns
        required = ["timestamp", "open", "high", "low", "close", "volume"]
        for col in required:
            if col not in df.columns:
                if col == "volume":
                    # Some forex data doesn't have volume
                    df["volume"] = 0
                else:
                    raise ValueError(f"Missing required column: {col}")

        # Convert types
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Sort by timestamp (oldest first)
        df = df.sort_values("timestamp").reset_index(drop=True)

        # Keep only required columns
        df = df[required]

        return df

    def _validate_data(self, df: pd.DataFrame) -> bool:
        """
        Validate OHLCV data quality.

        Checks:
        - Required columns present
        - No missing values in critical columns
        - High >= Low
        - Close within [Low, High]
        - Timestamps are sequential

        Args:
            df: DataFrame to validate

        Returns:
            True if valid, raises ValueError otherwise
        """
        required_columns = ["timestamp", "open", "high", "low", "close", "volume"]

        # Check required columns
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")

        # Check for missing OHLC values
        critical_cols = ["open", "high", "low", "close"]
        if df[critical_cols].isnull().any().any():
            null_counts = df[critical_cols].isnull().sum()
            raise ValueError(f"Missing values in critical columns:\n{null_counts}")

        # Validate high >= low
        invalid_high_low = df[df["high"] < df["low"]]
        if not invalid_high_low.empty:
            raise ValueError(
                f"Found {len(invalid_high_low)} rows where high < low:\n"
                f"{invalid_high_low[['timestamp', 'high', 'low']].head()}"
            )

        # Validate close within [low, high]
        invalid_close = df[(df["close"] < df["low"]) | (df["close"] > df["high"])]
        if not invalid_close.empty:
            raise ValueError(
                f"Found {len(invalid_close)} rows where close not in [low, high]:\n"
                f"{invalid_close[['timestamp', 'low', 'close', 'high']].head()}"
            )

        # Check timestamps are sequential (no duplicates)
        if df["timestamp"].duplicated().any():
            duplicates = df[df["timestamp"].duplicated(keep=False)]
            raise ValueError(
                f"Found {len(duplicates)} duplicate timestamps:\n"
                f"{duplicates['timestamp'].unique()[:5]}"
            )

        print("✓ Data validation passed")
        return True
