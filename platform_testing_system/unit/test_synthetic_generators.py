"""
Unit Tests for the Synthetic Data Generation Subsystem.

Verifies that MarketRegimeGenerator, PriceTickGenerator, AnomalyDataGenerator,
and MockNetworkDataFactory produce schema-valid, mathematically sound test data.
"""

from datetime import datetime, timezone
import numpy as np
import pandas as pd
import pytest

from platform_testing_system.synthetic_data.anomaly_generator import (
    AnomalyDataGenerator,
    AnomalyType,
)
from platform_testing_system.synthetic_data.market_regimes import (
    MarketRegimeGenerator,
    MarketRegimeType,
)
from platform_testing_system.synthetic_data.mock_network_data import (
    MockHttpResponse,
    MockNetworkDataFactory,
)
from platform_testing_system.synthetic_data.tick_generator import (
    PriceTick,
    PriceTickGenerator,
    TickPatternType,
)


class TestSyntheticDataGenerators:
    """Test suite verifying synthetic data generation modules."""

    @pytest.mark.parametrize("regime_type", list(MarketRegimeType))
    def test_market_regime_generator_all_types(self, regime_type: MarketRegimeType) -> None:
        """Verify each market regime generates valid non-empty DataFrame with proper OHLC relationships."""
        df = MarketRegimeGenerator.generate_regime(regime_type, count=60, base_price=4100.0)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 60
        required_cols = {"timestamp", "open", "high", "low", "close", "volume"}
        assert required_cols.issubset(set(df.columns))

        # Check OHLC bounds: low <= open <= high, low <= close <= high
        assert (df["low"] <= df["open"] + 1e-6).all(), f"Failed on {regime_type}"
        assert (df["low"] <= df["close"] + 1e-6).all(), f"Failed on {regime_type}"
        assert (df["high"] >= df["open"] - 1e-6).all(), f"Failed on {regime_type}"
        assert (df["high"] >= df["close"] - 1e-6).all(), f"Failed on {regime_type}"
        assert (df["volume"] >= 0).all()

    @pytest.mark.parametrize("pattern_type", list(TickPatternType))
    def test_price_tick_generator_all_patterns(self, pattern_type: TickPatternType) -> None:
        """Verify each tick stream pattern produces PriceTick objects."""
        ticks = PriceTickGenerator.generate_ticks(
            pattern=pattern_type,
            duration_seconds=10.0,
            ticks_per_second=4.0,
            start_price=4100.0,
        )
        assert len(ticks) == 40
        for tick in ticks:
            assert isinstance(tick, PriceTick)
            assert isinstance(tick.timestamp, datetime)
            assert tick.price > 0.0

    def test_price_tick_stream_iterator(self) -> None:
        """Verify stream_ticks generator yields PriceTicks sequentially."""
        stream = PriceTickGenerator.stream_ticks(duration_seconds=5.0, ticks_per_second=2.0)
        ticks = list(stream)
        assert len(ticks) == 10

    @pytest.mark.parametrize("anomaly_type", list(AnomalyType))
    def test_anomaly_data_generator_all_types(self, anomaly_type: AnomalyType) -> None:
        """Verify each anomaly scenario generates configured anomalies."""
        df = AnomalyDataGenerator.generate_anomaly(anomaly_type, count=40)
        assert isinstance(df, pd.DataFrame)
        if anomaly_type == AnomalyType.EMPTY_DATAFRAME:
            assert len(df) == 0
        elif anomaly_type == AnomalyType.SINGLE_ROW_DATAFRAME:
            assert len(df) == 1
        elif anomaly_type == AnomalyType.INSUFFICIENT_ROWS:
            assert len(df) == 10
        elif anomaly_type == AnomalyType.MISSING_CLOSE_COLUMN:
            assert "close" not in df.columns
        elif anomaly_type == AnomalyType.ALL_NAN_VALUES:
            assert df["close"].isna().all()
        elif anomaly_type == AnomalyType.ZERO_PRICES:
            assert (df["close"] == 0.0).all()
        elif anomaly_type == AnomalyType.NEGATIVE_PRICES:
            assert (df["close"] < 0.0).all()

    def test_mock_network_data_factory_payloads(self) -> None:
        """Verify MockNetworkDataFactory creates valid schemas."""
        b_price = MockNetworkDataFactory.create_binance_price_payload(4100.5)
        assert b_price["symbol"] == "PAXGUSDT"
        assert b_price["price"] == "4100.50"

        b_klines = MockNetworkDataFactory.create_binance_klines_payload(count=20)
        assert len(b_klines) == 20
        assert len(b_klines[0]) >= 6

        k_ticker = MockNetworkDataFactory.create_kraken_ticker_payload(4100.5)
        assert "PAXGUSD" in k_ticker["result"]

        y_chart = MockNetworkDataFactory.create_yahoo_chart_payload(price=4100.5)
        assert "chart" in y_chart

        o_order = MockNetworkDataFactory.create_olymp_trade_order_payload()
        assert o_order["status"] == "success"

        o_err = MockNetworkDataFactory.create_olymp_trade_error_payload("Test err")
        assert o_err["status"] == "error"

        mock_resp = MockHttpResponse(json_data={"ok": True}, status_code=200)
        assert mock_resp.status_code == 200
        assert mock_resp.json() == {"ok": True}
        assert b"ok" in mock_resp.content
