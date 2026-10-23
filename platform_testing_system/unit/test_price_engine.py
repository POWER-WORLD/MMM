"""
Unit Tests for Real-Time Gold Price Engine Module.

Verifies thread management, multi-source failover (Binance -> Kraken -> Yahoo),
callback dispatching, historical data retrieval, and timeout resilience.
"""

from datetime import datetime, timezone
import time
from typing import List, Tuple
from unittest.mock import MagicMock

import pandas as pd
import pytest

from core.price_engine import GoldPriceEngine
from platform_testing_system.synthetic_data.mock_network_data import (
    MockHttpResponse,
    MockNetworkDataFactory,
)


class TestGoldPriceEngine:
    """Test suite for GoldPriceEngine."""

    def test_price_engine_initialization(self) -> None:
        """Verify engine initializes with expected default configuration."""
        ticks: List[Tuple[datetime, float]] = []
        engine = GoldPriceEngine(
            on_price_update_callback=lambda ts, p: ticks.append((ts, p)),
            poll_interval_seconds=0.05,
        )
        assert engine.get_current_price() is None
        assert engine._polling_thread is None

    def test_binance_primary_fetch_success(self) -> None:
        """Verify engine successfully parses Binance Spot Gold price."""
        session_mock = MagicMock()
        payload = MockNetworkDataFactory.create_binance_price_payload(4105.75)
        session_mock.get.return_value = MockHttpResponse(json_data=payload, status_code=200)

        engine = GoldPriceEngine(
            on_price_update_callback=lambda ts, p: None,
            http_session=session_mock,
        )

        price = engine._fetch_current_price()
        assert price == 4105.75

    def test_failover_to_kraken_when_binance_fails(self) -> None:
        """Verify engine fails over to Kraken when Binance raises exception or returns error."""
        session_mock = MagicMock()

        def side_effect(url, *args, **kwargs):
            if "binance" in url:
                raise ConnectionError("Binance unreachable")
            if "kraken" in url:
                return MockHttpResponse(json_data=MockNetworkDataFactory.create_kraken_ticker_payload(4108.20))
            return MockHttpResponse(status_code=404)

        session_mock.get.side_effect = side_effect

        engine = GoldPriceEngine(
            on_price_update_callback=lambda ts, p: None,
            http_session=session_mock,
        )

        price = engine._fetch_current_price()
        assert price == 4108.20

    def test_failover_to_yahoo_when_binance_and_kraken_fail(self) -> None:
        """Verify engine fails over to Yahoo Finance chart API when Binance & Kraken fail."""
        session_mock = MagicMock()

        def side_effect(url, *args, **kwargs):
            if "binance" in url or "kraken" in url:
                return MockHttpResponse(status_code=503)
            if "finance.yahoo.com" in url:
                return MockHttpResponse(json_data=MockNetworkDataFactory.create_yahoo_chart_payload(price=4102.40))
            return MockHttpResponse(status_code=404)

        session_mock.get.side_effect = side_effect

        engine = GoldPriceEngine(
            on_price_update_callback=lambda ts, p: None,
            http_session=session_mock,
        )

        price = engine._fetch_current_price()
        assert price == 4102.40

    def test_historical_data_binance_primary(self) -> None:
        """Verify historical data extraction from Binance klines."""
        session_mock = MagicMock()
        klines = MockNetworkDataFactory.create_binance_klines_payload(count=40, base_price=4100.0)
        session_mock.get.return_value = MockHttpResponse(json_data=klines, status_code=200)

        engine = GoldPriceEngine(
            on_price_update_callback=lambda ts, p: None,
            http_session=session_mock,
        )

        df = engine.get_historical_data()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 40
        assert "close" in df.columns
        assert "timestamp" in df.columns

    def test_thread_start_and_stop_lifecycle(self) -> None:
        """Verify start and stop methods manage background thread correctly."""
        ticks: List[Tuple[datetime, float]] = []
        session_mock = MagicMock()
        session_mock.get.return_value = MockHttpResponse(
            json_data=MockNetworkDataFactory.create_binance_price_payload(4100.0)
        )

        engine = GoldPriceEngine(
            on_price_update_callback=lambda ts, p: ticks.append((ts, p)),
            poll_interval_seconds=0.02,
            http_session=session_mock,
        )

        engine.start()
        assert engine._polling_thread is not None
        assert engine._polling_thread.is_alive()

        # Duplicate start call should be safe and idempotent
        engine.start()

        # Let the thread run a few cycles
        time.sleep(0.08)
        engine.stop()

        assert not engine._polling_thread.is_alive()
        assert len(ticks) >= 1
        assert engine.get_current_price() == 4100.0

        # Duplicate stop call should be safe and idempotent
        engine.stop()
