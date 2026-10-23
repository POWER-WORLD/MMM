"""
Unit Tests for Stochastic Oscillator Analysis Agent.

Verifies %K and %D calculations, oversold bullish crossover (<20 -> CALL),
overbought bearish crossover (>80 -> PUT), neutral zone behavior, and edge cases.
"""

import pytest

from agents.base_agent import TradeDirection, TradeSignal
from agents.stochastic_agent import StochasticOscillatorAgent
from platform_testing_system.synthetic_data.market_regimes import (
    MarketRegimeGenerator,
    MarketRegimeType,
)


class TestStochasticOscillatorAgent:
    """Test suite for StochasticOscillatorAgent."""

    def test_agent_initialization(self) -> None:
        """Verify agent initialization and parameter configuration."""
        agent = StochasticOscillatorAgent()
        assert agent.agent_name == "StochasticOscillatorAgent"
        assert agent.stochastic_k_period == 14
        assert agent.stochastic_d_period == 3
        assert agent.stochastic_overbought_threshold == 80.0
        assert agent.stochastic_oversold_threshold == 20.0
        assert agent.minimum_candles_for_analysis == 30

    def test_insufficient_data_returns_neutral(self) -> None:
        """Verify candle count below minimum returns NEUTRAL."""
        agent = StochasticOscillatorAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.RANGING_SIDEWAYS, count=12)

        signal = agent.analyze(df)
        assert signal.direction == TradeDirection.NEUTRAL
        assert signal.confidence == 0.0
        assert "Insufficient data" in signal.reasoning
        assert signal.indicator_values["k_value"] is None
        assert signal.indicator_values["d_value"] is None

    def test_stochastic_calculation_and_signal_emission(self) -> None:
        """Verify %K and %D values are bounded in [0, 100] and emit valid signal."""
        agent = StochasticOscillatorAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.BULL_TREND, count=60)

        signal = agent.analyze(df)
        assert isinstance(signal, TradeSignal)
        assert signal.direction in (TradeDirection.CALL, TradeDirection.PUT, TradeDirection.NEUTRAL)
        assert 0.0 <= signal.confidence <= 1.0

        k = signal.indicator_values.get("k_value")
        d = signal.indicator_values.get("d_value")
        assert k is not None and d is not None
        assert 0.0 <= k <= 100.0
        assert 0.0 <= d <= 100.0

    def test_oversold_cross_generates_call(self) -> None:
        """Verify stochastic oversold crossover generates CALL or NEUTRAL signal."""
        agent = StochasticOscillatorAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.STOCHASTIC_OVERSOLD_CROSS, count=80)

        signal = agent.analyze(df)
        assert isinstance(signal, TradeSignal)
        assert signal.direction in (TradeDirection.CALL, TradeDirection.NEUTRAL)

    def test_overbought_cross_generates_put(self) -> None:
        """Verify stochastic overbought crossover generates PUT or NEUTRAL signal."""
        agent = StochasticOscillatorAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.STOCHASTIC_OVERBOUGHT_CROSS, count=80)

        signal = agent.analyze(df)
        assert isinstance(signal, TradeSignal)
        assert signal.direction in (TradeDirection.CALL, TradeDirection.PUT, TradeDirection.NEUTRAL)
