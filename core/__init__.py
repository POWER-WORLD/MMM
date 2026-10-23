"""
Core Module for Gold Trading Analysis Platform.

Provides the foundational components for real-time gold price acquisition,
candle construction, and thread-safe data storage.

Public API:
    - GoldPriceEngine: Polls gold futures prices via yfinance.
    - CandleBuilder: Aggregates ticks into fixed-interval OHLCV candles.
    - CandleData: Dataclass representing a single OHLCV candle.
    - PlatformDataStore: Thread-safe in-memory store for platform state.
"""

from core.candle_builder import CandleBuilder, CandleData
from core.data_store import PlatformDataStore
from core.price_engine import GoldPriceEngine

__all__: list[str] = [
    "GoldPriceEngine",
    "CandleBuilder",
    "CandleData",
    "PlatformDataStore",
]
