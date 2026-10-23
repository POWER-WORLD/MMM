"""
Unit Tests for Platform Configuration Module.

Tests configuration dataclass defaults, frozen immutability, directory
creation logic, and master PlatformConfiguration aggregation.
"""

from dataclasses import FrozenInstanceError
import os
import pytest

from config import (
    PLATFORM_CONFIG,
    AgentConfiguration,
    DashboardConfiguration,
    LoggingConfiguration,
    PlatformConfiguration,
    PriceEngineConfiguration,
    TradingConfiguration,
)


class TestPlatformConfiguration:
    """Test suite verifying PlatformConfiguration and sub-configurations."""

    def test_global_singleton_instance(self) -> None:
        """Verify PLATFORM_CONFIG is a valid PlatformConfiguration instance."""
        assert isinstance(PLATFORM_CONFIG, PlatformConfiguration)
        assert isinstance(PLATFORM_CONFIG.price_engine, PriceEngineConfiguration)
        assert isinstance(PLATFORM_CONFIG.trading, TradingConfiguration)
        assert isinstance(PLATFORM_CONFIG.agent, AgentConfiguration)
        assert isinstance(PLATFORM_CONFIG.dashboard, DashboardConfiguration)
        assert isinstance(PLATFORM_CONFIG.logging, LoggingConfiguration)

    def test_price_engine_defaults(self) -> None:
        """Verify price engine configuration parameters."""
        cfg = PLATFORM_CONFIG.price_engine
        assert cfg.GOLD_TICKER_SYMBOL == "GC=F"
        assert cfg.PRICE_POLL_INTERVAL_SECONDS == 3
        assert cfg.CANDLE_INTERVAL_SECONDS == 10
        assert cfg.HISTORICAL_DATA_PERIOD == "5d"
        assert cfg.HISTORICAL_DATA_INTERVAL == "1m"
        assert cfg.MAX_CANDLES_IN_MEMORY == 4320

    def test_trading_configuration_defaults(self) -> None:
        """Verify trading parameters adhere to 1-minute FTT rules."""
        cfg = PLATFORM_CONFIG.trading
        assert cfg.TRADE_DURATION_SECONDS == 60
        assert cfg.DEFAULT_TRADE_AMOUNT_USD == 1.0
        assert cfg.PAYOUT_PERCENTAGE == 0.82
        assert cfg.INITIAL_DEMO_BALANCE_USD == 10000.0
        assert cfg.MAXIMUM_CONCURRENT_TRADES == 1
        assert cfg.COOLDOWN_BETWEEN_TRADES_SECONDS == 10
        assert cfg.USE_OLYMP_TRADE_DEMO is True
        assert cfg.OLYMP_TRADE_AUTH_TOKEN == ""
        assert cfg.OLYMP_TRADE_ACCOUNT_ID == ""
        assert cfg.OLYMP_TRADE_ASSET == "gold"

    def test_agent_configuration_defaults(self) -> None:
        """Verify agent threshold parameters and indicator periods."""
        cfg = PLATFORM_CONFIG.agent
        assert cfg.TOTAL_AGENT_COUNT == 7
        assert cfg.REQUIRED_CONSENSUS_COUNT == 7
        assert cfg.MINIMUM_CONFIDENCE_THRESHOLD == 0.55
        assert cfg.MINIMUM_CANDLES_FOR_ANALYSIS == 30

        # RSI
        assert cfg.RSI_PERIOD == 14
        assert cfg.RSI_OVERBOUGHT_THRESHOLD == 70.0
        assert cfg.RSI_OVERSOLD_THRESHOLD == 30.0

        # MACD
        assert cfg.MACD_FAST_PERIOD == 12
        assert cfg.MACD_SLOW_PERIOD == 26
        assert cfg.MACD_SIGNAL_PERIOD == 9

        # Bollinger
        assert cfg.BOLLINGER_PERIOD == 20
        assert cfg.BOLLINGER_STANDARD_DEVIATION == 2.0

        # EMA
        assert cfg.EMA_SHORT_PERIOD == 9
        assert cfg.EMA_LONG_PERIOD == 21

        # Stochastic
        assert cfg.STOCHASTIC_K_PERIOD == 14
        assert cfg.STOCHASTIC_D_PERIOD == 3
        assert cfg.STOCHASTIC_OVERBOUGHT_THRESHOLD == 80.0
        assert cfg.STOCHASTIC_OVERSOLD_THRESHOLD == 20.0

        # ADX
        assert cfg.ADX_PERIOD == 14
        assert cfg.ADX_TREND_STRENGTH_THRESHOLD == 25.0

        # Ichimoku
        assert cfg.ICHIMOKU_CONVERSION_PERIOD == 9
        assert cfg.ICHIMOKU_BASE_PERIOD == 26
        assert cfg.ICHIMOKU_SPAN_B_PERIOD == 52
        assert cfg.ICHIMOKU_DISPLACEMENT == 26

    def test_dashboard_configuration_defaults(self) -> None:
        """Verify dashboard server configuration defaults."""
        cfg = PLATFORM_CONFIG.dashboard
        assert cfg.HOST == "127.0.0.1"
        assert cfg.PORT == 5000
        assert cfg.DEBUG_MODE is False
        assert len(cfg.SECRET_KEY) > 0

    def test_sub_configurations_are_immutable(self) -> None:
        """Verify dataclasses are frozen and raise FrozenInstanceError upon mutation."""
        with pytest.raises(FrozenInstanceError):
            PLATFORM_CONFIG.trading.TRADE_DURATION_SECONDS = 120  # type: ignore

        with pytest.raises(FrozenInstanceError):
            PLATFORM_CONFIG.agent.REQUIRED_CONSENSUS_COUNT = 5  # type: ignore

        with pytest.raises(FrozenInstanceError):
            PLATFORM_CONFIG.price_engine.CANDLE_INTERVAL_SECONDS = 30  # type: ignore

    def test_ensure_directories_exist(self) -> None:
        """Verify ensure_directories_exist creates logging directory."""
        PLATFORM_CONFIG.ensure_directories_exist()
        assert os.path.isdir(PLATFORM_CONFIG.logging.LOG_DIRECTORY)
