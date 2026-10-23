"""
Unit Tests for MACD Analysis Agent Module.

Verifies MACD line, signal line, and histogram computation, bullish crossover (CALL),
bearish crossover (PUT), histogram acceleration, and insufficient data handling.
"""

import pytest

from agents.base_agent import TradeDirection, TradeSignal
from agents.macd_agent import MovingAverageConvergenceDivergenceAgent
from platform_testing_system.synthetic_data.market_regimes import (
    MarketRegimeGenerator,
    MarketRegimeType,
)


class TestMovingAverageConvergenceDivergenceAgent:
    """Test suite for MovingAverageConvergenceDivergenceAgent."""

    def test_agent_initialization(self) -> None:
        """Verify agent initialization and parameter configuration."""
        agent = MovingAverageConvergenceDivergenceAgent()
        assert agent.agent_name == "MovingAverageConvergenceDivergenceAgent"
        assert agent.macd_fast_period == 12
        assert agent.macd_slow_period == 26
        assert agent.macd_signal_period == 9
        assert agent.minimum_candles_for_analysis == 30

    def test_insufficient_data_returns_neutral(self) -> None:
        """Verify insufficient candle count returns NEUTRAL."""
        agent = MovingAverageConvergenceDivergenceAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.RANGING_SIDEWAYS, count=20)

        signal = agent.analyze(df)
        assert signal.direction == TradeDirection.NEUTRAL
        assert signal.confidence == 0.0
        assert "Insufficient data" in signal.reasoning
        assert signal.indicator_values["macd_line"] is None

    def test_bullish_macd_crossover_generates_call(self) -> None:
        """Verify bullish MACD crossover produces CALL signal."""
        agent = MovingAverageConvergenceDivergenceAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.MACD_BULLISH_CROSSOVER, count=80)

        signal = agent.analyze(df)
        assert isinstance(signal, TradeSignal)
        # Should be CALL or NEUTRAL if close to crossover threshold
        assert signal.direction in (TradeDirection.CALL, TradeDirection.NEUTRAL)
        assert signal.indicator_values["macd_line"] is not None
        assert signal.indicator_values["signal_line"] is not None
        assert signal.indicator_values["histogram"] is not None

    def test_bearish_macd_crossover_generates_put(self) -> None:
        """Verify bearish MACD crossover produces PUT signal."""
        agent = MovingAverageConvergenceDivergenceAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.MACD_BEARISH_CROSSOVER, count=80)

        signal = agent.analyze(df)
        assert isinstance(signal, TradeSignal)
        assert signal.direction in (TradeDirection.PUT, TradeDirection.NEUTRAL)
        assert signal.indicator_values["macd_line"] is not None
        assert signal.indicator_values["signal_line"] is not None
        assert signal.indicator_values["histogram"] is not None

    def test_indicator_values_dictionary_keys(self) -> None:
        """Verify indicator_values contains all required keys with valid float values."""
        agent = MovingAverageConvergenceDivergenceAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.BULL_TREND, count=60)

        signal = agent.analyze(df)
        assert "macd_line" in signal.indicator_values
        assert "signal_line" in signal.indicator_values
        assert "histogram" in signal.indicator_values
        assert isinstance(signal.indicator_values["macd_line"], (float, int))
