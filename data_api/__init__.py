"""
Data API module for fetching and storing forex OHLCV data.

This module provides functionality to:
- Fetch real-time and historical forex data from various APIs
- Store and cache data locally
- Normalize data into a standard schema
"""

from .data_fetcher import ForexDataFetcher
from .data_store import DataStore

__all__ = ["ForexDataFetcher", "DataStore"]
