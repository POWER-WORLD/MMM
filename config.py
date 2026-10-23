"""
Platform Configuration Module for Gold Trading Analysis Platform.

Centralizes all configurable parameters including price engine settings,
trading parameters, agent thresholds, and dashboard configuration.
"""

import os
from dataclasses import dataclass, field
from typing import Final


@dataclass(frozen=True)
class PriceEngineConfiguration:
    """Configuration for the real-time price fetching engine."""

    GOLD_TICKER_SYMBOL: str = "GC=F"
    PRICE_POLL_INTERVAL_SECONDS: int = 3
    CANDLE_INTERVAL_SECONDS: int = 10
    HISTORICAL_DATA_PERIOD: str = "5d"
    HISTORICAL_DATA_INTERVAL: str = "1m"
    MAX_CANDLES_IN_MEMORY: int = 4320


@dataclass(frozen=True)
class TradingConfiguration:
    """Configuration for trade execution and management."""

    TRADE_DURATION_SECONDS: int = 60
    DEFAULT_TRADE_AMOUNT_USD: float = 1.0
    PAYOUT_PERCENTAGE: float = 0.82
    INITIAL_DEMO_BALANCE_USD: float = 10000.0
    MAXIMUM_CONCURRENT_TRADES: int = 1
    COOLDOWN_BETWEEN_TRADES_SECONDS: int = 10
    USE_OLYMP_TRADE_DEMO: bool = True
    OLYMP_TRADE_AUTH_TOKEN: str = ""
    OLYMP_TRADE_ACCOUNT_ID: str = ""
    OLYMP_TRADE_ASSET: str = "gold"


@dataclass(frozen=True)
class AgentConfiguration:
    """Configuration for the analysis agents and consensus engine."""

    TOTAL_AGENT_COUNT: int = 7
    REQUIRED_CONSENSUS_COUNT: int = 7
    MINIMUM_CONFIDENCE_THRESHOLD: float = 0.55
    MINIMUM_CANDLES_FOR_ANALYSIS: int = 30
    RSI_PERIOD: int = 14
    RSI_OVERBOUGHT_THRESHOLD: float = 70.0
    RSI_OVERSOLD_THRESHOLD: float = 30.0
    MACD_FAST_PERIOD: int = 12
    MACD_SLOW_PERIOD: int = 26
    MACD_SIGNAL_PERIOD: int = 9
    BOLLINGER_PERIOD: int = 20
    BOLLINGER_STANDARD_DEVIATION: float = 2.0
    EMA_SHORT_PERIOD: int = 9
    EMA_LONG_PERIOD: int = 21
    STOCHASTIC_K_PERIOD: int = 14
    STOCHASTIC_D_PERIOD: int = 3
    STOCHASTIC_OVERBOUGHT_THRESHOLD: float = 80.0
    STOCHASTIC_OVERSOLD_THRESHOLD: float = 20.0
    ADX_PERIOD: int = 14
    ADX_TREND_STRENGTH_THRESHOLD: float = 25.0
    ICHIMOKU_CONVERSION_PERIOD: int = 9
    ICHIMOKU_BASE_PERIOD: int = 26
    ICHIMOKU_SPAN_B_PERIOD: int = 52
    ICHIMOKU_DISPLACEMENT: int = 26


@dataclass(frozen=True)
class DashboardConfiguration:
    """Configuration for the web dashboard server."""

    HOST: str = "127.0.0.1"
    PORT: int = 5000
    DEBUG_MODE: bool = False
    SECRET_KEY: str = "gold-trading-platform-secret-key-2024"
    SOCKET_UPDATE_INTERVAL_SECONDS: float = 1.0


@dataclass(frozen=True)
class LoggingConfiguration:
    """Configuration for application logging."""

    LOG_DIRECTORY: str = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "logs"
    )
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


class PlatformConfiguration:
    """
    Master configuration class that aggregates all sub-configurations.

    Provides a single access point for all platform settings.
    All sub-configurations are immutable frozen dataclasses.
    """

    def __init__(self) -> None:
        self.price_engine: Final[PriceEngineConfiguration] = PriceEngineConfiguration()
        self.trading: Final[TradingConfiguration] = TradingConfiguration()
        self.agent: Final[AgentConfiguration] = AgentConfiguration()
        self.dashboard: Final[DashboardConfiguration] = DashboardConfiguration()
        self.logging: Final[LoggingConfiguration] = LoggingConfiguration()

    def ensure_directories_exist(self) -> None:
        """Create all required directories if they do not exist."""
        os.makedirs(self.logging.LOG_DIRECTORY, exist_ok=True)


# Global singleton configuration instance
PLATFORM_CONFIG: Final[PlatformConfiguration] = PlatformConfiguration()
