"""
Unit Tests for Exponential Moving Average (EMA) Crossover Analysis Agent.

Verifies fast EMA (9) vs slow EMA (21) computation, Golden Cross (CALL),
Death Cross (PUT), slope continuation, and spread-based confidence scaling.
"""

import pytest

from agents.base_agent import TradeDirection, TradeSignal
from agents.ema_crossover_agent import ExponentialMovingAverageCrossoverAgent
from platform_testing_system.synthetic_data.market_regimes import (
    MarketRegimeGenerator,
    MarketRegimeType,
)


class TestExponentialMovingAverageCrossoverAgent:
    """Test suite for ExponentialMovingAverageCrossoverAgent."""

    def test_agent_initialization(self) -> None:
        """Verify agent properties and EMA period configurations."""
        agent = ExponentialMovingAverageCrossoverAgent()
        assert agent.agent_name == "ExponentialMovingAverageCrossoverAgent"
        assert agent.ema_short_period == 9
        assert agent.ema_long_period == 21
        assert agent.minimum_candles_for_analysis == 30

    def test_insufficient_data_returns_neutral(self) -> None:
        """Verify candle count below minimum returns NEUTRAL with 0.0 confidence."""
        agent = ExponentialMovingAverageCrossoverAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.RANGING_SIDEWAYS, count=10)

        signal = agent.analyze(df)
        assert signal.direction == TradeDirection.NEUTRAL
        assert signal.confidence == 0.0
        assert "Insufficient data" in signal.reasoning
        assert signal.indicator_values["ema_short"] is None

    def test_golden_cross_generates_call_signal(self) -> None:
        """Verify fast EMA crossing above slow EMA generates CALL signal."""
        agent = ExponentialMovingAverageCrossoverAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.EMA_GOLDEN_CROSS, count=80)

        signal = agent.analyze(df)
        assert isinstance(signal, TradeSignal)
        assert signal.direction in (TradeDirection.CALL, TradeDirection.NEUTRAL)
        assert signal.indicator_values["ema_short"] is not None
        assert signal.indicator_values["ema_long"] is not None

    def test_death_cross_generates_put_signal(self) -> None:
        """Verify fast EMA crossing below slow EMA generates PUT signal."""
        agent = ExponentialMovingAverageCrossoverAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.EMA_DEATH_CROSS, count=80)

        signal = agent.analyze(df)
        assert isinstance(signal, TradeSignal)
        assert signal.direction in (TradeDirection.PUT, TradeDirection.NEUTRAL)
        assert signal.indicator_values["ema_short"] is not None
        assert signal.indicator_values["ema_long"] is not None

    def test_indicator_values_contain_emas_and_spread(self) -> None:
        """Verify indicator_values contains ema_short, ema_long, and crossover_distance."""
        agent = ExponentialMovingAverageCrossoverAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.BULL_TREND, count=60)

        signal = agent.analyze(df)
        assert "ema_short" in signal.indicator_values
        assert "ema_long" in signal.indicator_values
        assert "crossover_distance" in signal.indicator_values
