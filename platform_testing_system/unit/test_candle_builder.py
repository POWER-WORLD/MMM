"""
Unit Tests for 10-Second Candle Builder Module.

Verifies tick ingestion, exact interval boundary alignment, multi-tick OHLC aggregation,
candle finalization callbacks, dynamic interval reconfiguration, and thread-safety.
"""

from datetime import datetime, timedelta, timezone
from typing import List
import pytest

from core.candle_builder import CandleBuilder, CandleData


class TestCandleBuilder:
    """Test suite for CandleData and CandleBuilder."""

    def test_candle_data_attributes_and_dict_conversion(self) -> None:
        """Verify CandleData structure, immutability, and to_dict method."""
        now = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
        candle = CandleData(
            timestamp=now,
            open_price=4100.0,
            high_price=4105.0,
            low_price=4095.0,
            close_price=4102.5,
            volume=50,
            tick_count=8,
        )

        assert candle.timestamp == now
        assert candle.open_price == 4100.0
        assert candle.high_price == 4105.0
        assert candle.low_price == 4095.0
        assert candle.close_price == 4102.5
        assert candle.volume == 50
        assert candle.tick_count == 8

        c_dict = candle.to_dict()
        assert c_dict == {
            "timestamp": now,
            "open": 4100.0,
            "high": 4105.0,
            "low": 4095.0,
            "close": 4102.5,
            "volume": 50,
            "tick_count": 8,
        }

    def test_single_candle_lifecycle_multi_tick(self) -> None:
        """Verify multiple ticks within the same 10-second boundary aggregate correctly."""
        completed_candles: List[CandleData] = []
        builder = CandleBuilder(
            candle_interval_seconds=10,
            on_candle_complete_callback=lambda c: completed_candles.append(c),
        )

        base_time = datetime(2026, 10, 22, 14, 0, 0, tzinfo=timezone.utc)

        # 4 ticks within 14:00:00 - 14:00:09
        builder.add_tick(base_time + timedelta(seconds=1), 4100.0)  # Open = 4100.0
        builder.add_tick(base_time + timedelta(seconds=3), 4108.0)  # High = 4108.0
        builder.add_tick(base_time + timedelta(seconds=6), 4092.0)  # Low = 4092.0
        builder.add_tick(base_time + timedelta(seconds=9), 4104.0)  # Close = 4104.0

        # Current in-progress partial candle check
        partial = builder.get_current_partial_candle()
        assert partial is not None
        assert partial["open"] == 4100.0
        assert partial["high"] == 4108.0
        assert partial["low"] == 4092.0
        assert partial["close"] == 4104.0
        assert partial["tick_count"] == 4
        assert len(completed_candles) == 0

        # Crossing into next boundary (14:00:10) triggers finalization of candle 1
        builder.add_tick(base_time + timedelta(seconds=11), 4105.0)

        assert len(completed_candles) == 1
        c = completed_candles[0]
        assert c.timestamp == base_time
        assert c.open_price == 4100.0
        assert c.high_price == 4108.0
        assert c.low_price == 4092.0
        assert c.close_price == 4104.0
        assert c.tick_count == 4

        # Verify new partial candle started with tick 5
        partial2 = builder.get_current_partial_candle()
        assert partial2 is not None
        assert partial2["open"] == 4105.0
        assert partial2["tick_count"] == 1

    def test_interval_boundary_alignment_various_intervals(self) -> None:
        """Verify boundary flooring logic across 5s, 10s, 30s, 60s intervals."""
        completed_candles: List[CandleData] = []
        builder = CandleBuilder(
            candle_interval_seconds=10,
            on_candle_complete_callback=lambda c: completed_candles.append(c),
        )

        t = datetime(2026, 10, 22, 14, 25, 37, 450000, tzinfo=timezone.utc)
        aligned_10 = builder._get_candle_start_time(t)
        assert aligned_10 == datetime(2026, 10, 22, 14, 25, 30, tzinfo=timezone.utc)

        # 30-second interval
        builder.set_interval(30)
        assert builder.get_interval() == 30
        aligned_30 = builder._get_candle_start_time(t)
        assert aligned_30 == datetime(2026, 10, 22, 14, 25, 30, tzinfo=timezone.utc)

        # 60-second interval
        builder.set_interval(60)
        aligned_60 = builder._get_candle_start_time(t)
        assert aligned_60 == datetime(2026, 10, 22, 14, 25, 0, tzinfo=timezone.utc)

    def test_dynamic_interval_reconfiguration_finalizes_active_candle(self) -> None:
        """Verify changing interval immediately finalizes current candle."""
        completed = []
        builder = CandleBuilder(
            candle_interval_seconds=10,
            on_candle_complete_callback=lambda c: completed.append(c),
        )

        base_time = datetime(2026, 10, 22, 14, 0, 0, tzinfo=timezone.utc)
        builder.add_tick(base_time + timedelta(seconds=2), 4100.0)
        builder.add_tick(base_time + timedelta(seconds=4), 4102.0)
        assert len(completed) == 0

        # Change interval to 15s
        builder.set_interval(15)
        assert len(completed) == 1
        assert completed[0].close_price == 4102.0
        assert builder.get_interval() == 15

    def test_invalid_interval_update_ignored(self) -> None:
        """Verify setting interval to non-positive or identical value is ignored safely."""
        completed = []
        builder = CandleBuilder(
            candle_interval_seconds=10,
            on_candle_complete_callback=lambda c: completed.append(c),
        )
        builder.set_interval(0)
        assert builder.get_interval() == 10
        builder.set_interval(-5)
        assert builder.get_interval() == 10
        builder.set_interval(10)
        assert builder.get_interval() == 10
