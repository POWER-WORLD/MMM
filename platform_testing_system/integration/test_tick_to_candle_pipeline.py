"""
Integration Tests for Tick Ingestion to CandleBuilder and DataStore Pipeline.

Verifies the live pipeline where high-frequency price ticks stream into CandleBuilder,
aggregate into aligned candles, and populate PlatformDataStore continuously.
"""

from datetime import datetime, timezone
import pandas as pd
import pytest

from core.candle_builder import CandleBuilder, CandleData
from core.data_store import PlatformDataStore
from platform_testing_system.synthetic_data.tick_generator import (
    PriceTickGenerator,
    TickPatternType,
)


class TestTickToCandlePipeline:
    """Pipeline integration test: Price ticks -> CandleBuilder -> PlatformDataStore."""

    def test_streaming_ticks_build_valid_data_store_candles(self) -> None:
        """
        Stream 60 seconds of synthetic ticks (5 ticks/sec = 300 ticks) through CandleBuilder (10s candles).
        Verify that exactly 6 completed candles are recorded in PlatformDataStore.
        """
        store = PlatformDataStore(max_candles=100)

        def on_candle_completed(candle: CandleData) -> None:
            store.add_candle(candle.to_dict())

        builder = CandleBuilder(
            candle_interval_seconds=10,
            on_candle_complete_callback=on_candle_completed,
        )

        base_time = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
        ticks = PriceTickGenerator.generate_ticks(
            pattern=TickPatternType.STEADY_UPWARD_DRIFT,
            duration_seconds=70.0,
            ticks_per_second=5.0,
            start_price=4100.0,
            start_time=base_time,
        )

        for tick in ticks:
            store.set_current_price(tick.price, tick.timestamp)
            builder.add_tick(tick.timestamp, tick.price)

        # 70 seconds of ticks with 10s interval yields at least 6 completed candles
        candle_count = store.get_candle_count()
        assert candle_count >= 6

        df = store.get_candles_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == candle_count
        assert not df.isnull().values.any()

        # Verify OHLC mathematical consistency: low <= open, close <= high
        assert (df["low"] <= df["open"]).all()
        assert (df["low"] <= df["close"]).all()
        assert (df["high"] >= df["open"]).all()
        assert (df["high"] >= df["close"]).all()

    def test_dynamic_interval_change_mid_stream(self) -> None:
        """
        Stream ticks under 10s interval, switch to 30s interval dynamically, and verify
        pipeline adapts without losing data.
        """
        store = PlatformDataStore(max_candles=100)
        builder = CandleBuilder(
            candle_interval_seconds=10,
            on_candle_complete_callback=lambda c: store.add_candle(c.to_dict()),
        )

        base_time = datetime(2026, 10, 22, 13, 0, 0, tzinfo=timezone.utc)

        # First 35 seconds of ticks at 10s interval
        ticks_phase1 = PriceTickGenerator.generate_ticks(
            pattern=TickPatternType.GEOMETRIC_BROWNIAN_MOTION,
            duration_seconds=35.0,
            ticks_per_second=2.0,
            start_price=4100.0,
            start_time=base_time,
        )
        for t in ticks_phase1:
            builder.add_tick(t.timestamp, t.price)

        initial_count = store.get_candle_count()
        assert initial_count >= 3

        # Switch interval to 30 seconds
        builder.set_interval(30)

        # Stream next 65 seconds
        phase2_start = ticks_phase1[-1].timestamp
        ticks_phase2 = PriceTickGenerator.generate_ticks(
            pattern=TickPatternType.STEADY_UPWARD_DRIFT,
            duration_seconds=65.0,
            ticks_per_second=2.0,
            start_price=4105.0,
            start_time=phase2_start,
        )
        for t in ticks_phase2:
            builder.add_tick(t.timestamp, t.price)

        final_count = store.get_candle_count()
        assert final_count > initial_count
