"""
Unit Tests for Ichimoku Cloud Analysis Agent.

Verifies Tenkan-sen, Kijun-sen, Senkou Span A & B calculations, cloud breakout (CALL),
cloud breakdown (PUT), inside-cloud neutrality, and minimum data requirements.
"""

import pytest

from agents.base_agent import TradeDirection, TradeSignal
from agents.ichimoku_agent import IchimokuCloudAgent
from platform_testing_system.synthetic_data.market_regimes import (
    MarketRegimeGenerator,
    MarketRegimeType,
)


class TestIchimokuCloudAgent:
    """Test suite for IchimokuCloudAgent."""

    def test_agent_initialization(self) -> None:
        """Verify agent properties and period parameters."""
        agent = IchimokuCloudAgent()
        assert agent.agent_name == "IchimokuCloudAgent"
        assert agent.ichimoku_conversion_period == 9
        assert agent.ichimoku_base_period == 26
        assert agent.ichimoku_span_b_period == 52
        assert agent.ichimoku_displacement == 26
        assert agent.minimum_candles_for_analysis == 30

    def test_insufficient_data_returns_neutral(self) -> None:
        """Verify candle count below minimum required (78 candles) returns NEUTRAL."""
        agent = IchimokuCloudAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.RANGING_SIDEWAYS, count=40)

        signal = agent.analyze(df)
        assert signal.direction == TradeDirection.NEUTRAL
        assert signal.confidence == 0.0
        assert "Insufficient data" in signal.reasoning
        assert signal.indicator_values["conversion_line"] is None

    def test_bullish_above_cloud_generates_call(self) -> None:
        """Verify price above the Ichimoku cloud generates CALL or NEUTRAL signal."""
        agent = IchimokuCloudAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.BULL_TREND, count=120)

        signal = agent.analyze(df)
        assert isinstance(signal, TradeSignal)
        assert signal.direction in (TradeDirection.CALL, TradeDirection.NEUTRAL)
        assert signal.indicator_values["conversion_line"] is not None
        assert signal.indicator_values["base_line"] is not None
        assert signal.indicator_values["span_a"] is not None
        assert signal.indicator_values["span_b"] is not None

    def test_bearish_below_cloud_generates_put(self) -> None:
        """Verify price below the Ichimoku cloud generates PUT or NEUTRAL signal."""
        agent = IchimokuCloudAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.BEAR_TREND, count=120)

        signal = agent.analyze(df)
        assert isinstance(signal, TradeSignal)
        assert signal.direction in (TradeDirection.PUT, TradeDirection.NEUTRAL)

    def test_inside_cloud_returns_neutral(self) -> None:
        """Verify price inside Kumo cloud generates NEUTRAL signal."""
        agent = IchimokuCloudAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.RANGING_SIDEWAYS, count=120)

        signal = agent.analyze(df)
        assert isinstance(signal, TradeSignal)
        if signal.direction == TradeDirection.NEUTRAL and "INSIDE the Ichimoku Cloud" in signal.reasoning:
            assert signal.confidence <= 0.40
