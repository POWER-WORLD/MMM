"""
Global Pytest Configuration and Shared Test Fixtures.

Provides isolated test doubles, mock dependencies, pre-computed synthetic data,
and environment setup for all test modules within platform_testing_system.
"""

from datetime import datetime, timezone
from typing import Dict, List, Tuple
from unittest.mock import MagicMock

import pandas as pd
import pytest

from agents.adx_agent import AverageDirectionalIndexAgent
from agents.base_agent import BaseAnalysisAgent, TradeDirection, TradeSignal
from agents.bollinger_agent import BollingerBandsAgent
from agents.consensus_engine import ConsensusEngine
from agents.ema_crossover_agent import ExponentialMovingAverageCrossoverAgent
from agents.ichimoku_agent import IchimokuCloudAgent
from agents.macd_agent import MovingAverageConvergenceDivergenceAgent
from agents.rsi_agent import RelativeStrengthIndexAgent
from agents.stochastic_agent import StochasticOscillatorAgent
from config import PLATFORM_CONFIG, PlatformConfiguration
from core.candle_builder import CandleBuilder, CandleData
from core.data_store import PlatformDataStore
from dashboard.app import create_dashboard_application
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
from trading.olymptrade_client import OlympTradeClient
from trading.performance_tracker import PerformanceTracker
from trading.trade_executor import TradeExecutor


@pytest.fixture
def platform_config() -> PlatformConfiguration:
    """Fixture returning platform configuration singleton."""
    return PLATFORM_CONFIG


@pytest.fixture
def fresh_data_store() -> PlatformDataStore:
    """Fixture returning an isolated, empty PlatformDataStore."""
    return PlatformDataStore(max_candles=500)


@pytest.fixture
def candle_collector() -> Tuple[List[CandleData], CandleBuilder]:
    """
    Fixture providing a list collecting finalized candles and the configured CandleBuilder.
    """
    completed_candles: List[CandleData] = []
    builder = CandleBuilder(
        candle_interval_seconds=10,
        on_candle_complete_callback=lambda c: completed_candles.append(c),
    )
    return completed_candles, builder


@pytest.fixture
def all_seven_agents() -> List[BaseAnalysisAgent]:
    """Fixture providing freshly instantiated instances of all 7 analysis agents."""
    return [
        RelativeStrengthIndexAgent(),
        MovingAverageConvergenceDivergenceAgent(),
        BollingerBandsAgent(),
        ExponentialMovingAverageCrossoverAgent(),
        StochasticOscillatorAgent(),
        AverageDirectionalIndexAgent(),
        IchimokuCloudAgent(),
    ]


@pytest.fixture
def fresh_consensus_engine(all_seven_agents: List[BaseAnalysisAgent]) -> ConsensusEngine:
    """Fixture providing ConsensusEngine initialized with 7 agents requiring 7/7 agreement."""
    return ConsensusEngine(agents=all_seven_agents, required_consensus_count=7)


@pytest.fixture
def fresh_trade_executor() -> TradeExecutor:
    """Fixture providing TradeExecutor with clean $10,000 balance and 82% payout."""
    return TradeExecutor(initial_balance=10000.0, payout_percentage=0.82)


@pytest.fixture
def fresh_performance_tracker() -> PerformanceTracker:
    """Fixture providing PerformanceTracker with $10,000 initial balance."""
    return PerformanceTracker(initial_balance=10000.0)


@pytest.fixture
def fresh_olymp_client() -> OlympTradeClient:
    """Fixture providing OlympTradeClient in simulated mode."""
    return OlympTradeClient(use_simulated_mode=True)


@pytest.fixture
def mock_network_session() -> MagicMock:
    """Fixture providing a mock requests.Session pre-configured with valid Binance & Yahoo responses."""
    session_mock = MagicMock()

    def mock_get(url: str, *args, **kwargs):
        if "binance.com/api/v3/ticker/price" in url:
            return MockHttpResponse(json_data=MockNetworkDataFactory.create_binance_price_payload(4105.50))
        if "binance.com/api/v3/klines" in url:
            return MockHttpResponse(json_data=MockNetworkDataFactory.create_binance_klines_payload(count=60))
        if "kraken.com" in url:
            return MockHttpResponse(json_data=MockNetworkDataFactory.create_kraken_ticker_payload(4105.50))
        if "finance.yahoo.com" in url:
            return MockHttpResponse(json_data=MockNetworkDataFactory.create_yahoo_chart_payload(price=4105.50))
        return MockHttpResponse(json_data={}, status_code=404)

    session_mock.get.side_effect = mock_get
    return session_mock


@pytest.fixture
def flask_test_client(fresh_data_store: PlatformDataStore):
    """Fixture providing Flask test client configured with mock callbacks."""
    mock_state = {
        "current_price": 4100.50,
        "price_timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "candles": [{"time": 1700000000, "open": 4100.0, "high": 4102.0, "low": 4099.0, "close": 4101.0}],
        "agent_signals": [],
        "consensus": {},
        "performance": {"total_trades": 0, "winning_trades": 0, "losing_trades": 0, "success_rate": 0.0},
        "recent_trades": [],
        "active_trade": None,
        "current_balance": 10000.0,
    }
    app, socket_io = create_dashboard_application(
        get_state_callback=lambda: mock_state,
        get_config_callback=lambda: {"candle_interval_seconds": 10, "trade_duration_seconds": 60, "trade_amount_usd": 1.0},
        update_config_callback=lambda cfg: cfg,
    )
    app.config["TESTING"] = True
    return app.test_client(), socket_io


@pytest.fixture
def synthetic_regimes() -> Dict[MarketRegimeType, pd.DataFrame]:
    """Fixture generating a comprehensive dictionary of all market regime DataFrames."""
    return {
        regime: MarketRegimeGenerator.generate_regime(regime, count=100)
        for regime in MarketRegimeType
    }


@pytest.fixture
def adversarial_datasets() -> Dict[AnomalyType, pd.DataFrame]:
    """Fixture generating all anomaly scenario DataFrames."""
    return {
        anomaly: AnomalyDataGenerator.generate_anomaly(anomaly, count=50)
        for anomaly in AnomalyType
    }
