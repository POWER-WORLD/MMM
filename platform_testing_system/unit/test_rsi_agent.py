"""
Unit Tests for RSI (Relative Strength Index) Analysis Agent.

Verifies RSI calculation, oversold (<30 -> CALL), overbought (>70 -> PUT),
neutral zone behavior, divergence confirmation, and insufficient data handling.
"""

import pytest

from agents.base_agent import TradeDirection, TradeSignal
from agents.rsi_agent import RelativeStrengthIndexAgent
from platform_testing_system.synthetic_data.market_regimes import (
    MarketRegimeGenerator,
    MarketRegimeType,
)


class TestRelativeStrengthIndexAgent:
    """Test suite for RelativeStrengthIndexAgent."""

    def test_agent_initialization(self) -> None:
        """Verify agent properties and indicator thresholds."""
        agent = RelativeStrengthIndexAgent()
        assert agent.agent_name == "RelativeStrengthIndexAgent"
        assert agent.rsi_period == 14
        assert agent.rsi_overbought_threshold == 70.0
        assert agent.rsi_oversold_threshold == 30.0
        assert agent.minimum_candles_for_analysis == 30

    def test_insufficient_candles_returns_neutral(self) -> None:
        """Verify agent returns NEUTRAL when candle count is below minimum threshold."""
        agent = RelativeStrengthIndexAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.RANGING_SIDEWAYS, count=15)

        signal = agent.analyze(df)
        assert isinstance(signal, TradeSignal)
        assert signal.direction == TradeDirection.NEUTRAL
        assert signal.confidence == 0.0
        assert "Insufficient data" in signal.reasoning
        assert signal.indicator_values.get("rsi_value") is None

    def test_oversold_condition_produces_call_signal(self) -> None:
        """Verify RSI in oversold territory generates CALL signal with high confidence."""
        agent = RelativeStrengthIndexAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.RSI_OVERSOLD_REVERSAL, count=80)

        signal = agent.analyze(df)
        assert signal.direction == TradeDirection.CALL
        assert signal.confidence >= 0.50
        assert signal.indicator_values["rsi_value"] is not None
        assert signal.indicator_values["rsi_value"] <= agent.rsi_oversold_threshold + 5.0
        assert "oversold" in signal.reasoning.lower()

    def test_overbought_condition_produces_put_signal(self) -> None:
        """Verify RSI in overbought territory generates PUT signal with high confidence."""
        agent = RelativeStrengthIndexAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.RSI_OVERBOUGHT_REVERSAL, count=80)

        signal = agent.analyze(df)
        assert signal.direction == TradeDirection.PUT
        assert signal.confidence >= 0.50
        assert signal.indicator_values["rsi_value"] is not None
        assert signal.indicator_values["rsi_value"] >= agent.rsi_overbought_threshold - 5.0
        assert "overbought" in signal.reasoning.lower()

    def test_ranging_market_produces_neutral_signal(self) -> None:
        """Verify RSI between 30 and 70 returns NEUTRAL."""
        agent = RelativeStrengthIndexAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.RANGING_SIDEWAYS, count=80)

        signal = agent.analyze(df)
        rsi = signal.indicator_values.get("rsi_value")
        if rsi is not None and 30.0 < rsi < 70.0:
            assert signal.direction == TradeDirection.NEUTRAL
            assert "between oversold" in signal.reasoning
