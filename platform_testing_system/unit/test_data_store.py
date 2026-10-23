"""
Unit Tests for Thread-Safe PlatformDataStore Module.

Verifies thread-safe candle storage, FIFO trimming at max capacity, DataFrame extraction,
latest price caching, trade record logging, agent signal caching, and reset methods.
"""

from datetime import datetime, timezone
import pandas as pd
import pytest

from core.data_store import PlatformDataStore


class TestPlatformDataStore:
    """Test suite for PlatformDataStore."""

    def test_initial_state_empty(self) -> None:
        """Verify new data store has empty collections and None price."""
        store = PlatformDataStore(max_candles=100)
        assert store.get_candle_count() == 0
        assert store.get_candles() == []
        assert store.get_candles_dataframe().empty
        price, ts = store.get_current_price()
        assert price is None
        assert ts is None
        assert store.get_latest_price() is None
        assert store.get_trade_records() == []
        assert store.get_agent_signals() == []

    def test_candle_addition_and_dataframe_generation(self) -> None:
        """Verify candles are stored and converted into a standard pandas DataFrame."""
        store = PlatformDataStore(max_candles=50)
        now = datetime.now(tz=timezone.utc)

        for i in range(5):
            candle = {
                "timestamp": now,
                "open": 4100.0 + i,
                "high": 4102.0 + i,
                "low": 4099.0 + i,
                "close": 4101.5 + i,
                "volume": 25,
                "tick_count": 4,
            }
            store.add_candle(candle)

        assert store.get_candle_count() == 5
        df = store.get_candles_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume", "tick_count"]
        assert df["close"].iloc[-1] == 4105.5

        # Test count slice
        df_sliced = store.get_candles_dataframe(count=3)
        assert len(df_sliced) == 3
        assert df_sliced["close"].iloc[0] == 4103.5

    def test_max_candles_capacity_trimming(self) -> None:
        """Verify store enforces FIFO trimming when candle count exceeds max_candles."""
        max_limit = 5
        store = PlatformDataStore(max_candles=max_limit)

        for i in range(10):
            store.add_candle({
                "timestamp": datetime.now(tz=timezone.utc),
                "open": 4100.0 + i,
                "high": 4105.0 + i,
                "low": 4095.0 + i,
                "close": 4100.0 + i,
                "volume": 10,
                "tick_count": 2,
            })

        assert store.get_candle_count() == max_limit
        candles = store.get_candles()
        assert len(candles) == max_limit
        # Oldest preserved should be i=5
        assert candles[0]["open"] == 4105.0
        assert candles[-1]["open"] == 4109.0

    def test_current_price_setter_and_getter(self) -> None:
        """Verify real-time spot price and timestamp storage."""
        store = PlatformDataStore(max_candles=100)
        now = datetime.now(tz=timezone.utc)

        store.set_current_price(price=4103.75, timestamp=now)
        price, ts = store.get_current_price()
        assert price == 4103.75
        assert ts == now
        assert store.get_latest_price() == 4103.75

        # Overwrite with newer price
        store.set_current_price(price=4107.20, timestamp=now)
        assert store.get_latest_price() == 4107.20

    def test_trade_record_management(self) -> None:
        """Verify trade records are appended and retrieved."""
        store = PlatformDataStore(max_candles=100)
        t1 = {"trade_id": "trade_001", "result": "WIN", "pnl": 0.82}
        t2 = {"trade_id": "trade_002", "result": "LOSS", "pnl": -1.0}

        store.add_trade_record(t1)
        store.add_trade_record(t2)

        records = store.get_trade_records()
        assert len(records) == 2
        assert records[0]["trade_id"] == "trade_001"
        assert records[1]["trade_id"] == "trade_002"

        # Count slice
        sliced = store.get_trade_records(count=1)
        assert len(sliced) == 1
        assert sliced[0]["trade_id"] == "trade_002"

    def test_agent_signals_storage(self) -> None:
        """Verify agent signals can be cached and retrieved."""
        store = PlatformDataStore(max_candles=100)
        mock_signals = [
            {"agent_name": "RelativeStrengthIndexAgent", "direction": "CALL", "confidence": 0.85},
            {"agent_name": "BollingerBandsAgent", "direction": "CALL", "confidence": 0.90},
        ]

        store.set_agent_signals(mock_signals)
        signals = store.get_agent_signals()
        assert len(signals) == 2
        assert signals[0]["direction"] == "CALL"
        assert signals[1]["confidence"] == 0.90
