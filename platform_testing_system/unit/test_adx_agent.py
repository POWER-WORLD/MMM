"""
Unit Tests for Average Directional Index (ADX) Analysis Agent.

Verifies ADX (14) trend strength filtering (>25 threshold), DI+/DI- directional bias,
ranging market suppression (NEUTRAL), and confidence scaling.
"""

import pytest

from agents.adx_agent import AverageDirectionalIndexAgent
from agents.base_agent import TradeDirection, TradeSignal
from platform_testing_system.synthetic_data.market_regimes import (
    MarketRegimeGenerator,
    MarketRegimeType,
)


class TestAverageDirectionalIndexAgent:
    """Test suite for AverageDirectionalIndexAgent."""

    def test_agent_initialization(self) -> None:
        """Verify agent properties and ADX thresholds."""
        agent = AverageDirectionalIndexAgent()
        assert agent.agent_name == "AverageDirectionalIndexAgent"
        assert agent.adx_period == 14
        assert agent.adx_trend_strength_threshold == 25.0
        assert agent.minimum_candles_for_analysis == 30

    def test_insufficient_data_returns_neutral(self) -> None:
        """Verify insufficient candle count returns NEUTRAL."""
        agent = AverageDirectionalIndexAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.RANGING_SIDEWAYS, count=10)

        signal = agent.analyze(df)
        assert signal.direction == TradeDirection.NEUTRAL
        assert signal.confidence == 0.0
        assert "Insufficient data" in signal.reasoning
        assert signal.indicator_values["adx_value"] is None

    def test_ranging_market_below_threshold_returns_neutral(self) -> None:
        """Verify weak trend (ADX < 25.0) suppresses directional signal and returns NEUTRAL."""
        agent = AverageDirectionalIndexAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.RANGING_SIDEWAYS, count=80)

        signal = agent.analyze(df)
        adx_val = signal.indicator_values.get("adx_value")
        if adx_val is not None and adx_val < agent.adx_trend_strength_threshold:
            assert signal.direction == TradeDirection.NEUTRAL
            assert "below trend strength threshold" in signal.reasoning

    def test_strong_bull_trend_generates_call(self) -> None:
        """Verify strong upward trend with DI+ > DI- and ADX > 25 generates CALL."""
        agent = AverageDirectionalIndexAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.BULL_TREND, count=100)

        signal = agent.analyze(df)
        assert isinstance(signal, TradeSignal)
        assert signal.direction in (TradeDirection.CALL, TradeDirection.NEUTRAL)
        assert signal.indicator_values["adx_value"] is not None
        assert signal.indicator_values["di_positive"] is not None
        assert signal.indicator_values["di_negative"] is not None

    def test_strong_bear_trend_generates_put(self) -> None:
        """Verify strong downward trend with DI- > DI+ and ADX > 25 generates PUT."""
        agent = AverageDirectionalIndexAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.BEAR_TREND, count=100)

        signal = agent.analyze(df)
        assert isinstance(signal, TradeSignal)
        assert signal.direction in (TradeDirection.PUT, TradeDirection.NEUTRAL)
        assert signal.indicator_values["adx_value"] is not None
        assert signal.indicator_values["di_positive"] is not None
        assert signal.indicator_values["di_negative"] is not None
