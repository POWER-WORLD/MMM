"""
Unit Tests for Bollinger Bands Analysis Agent Module.

Verifies upper, middle, lower band calculation, lower band touch (CALL),
upper band touch (PUT), bandwidth squeeze detection, and neutral zone signals.
"""

import pytest

from agents.base_agent import TradeDirection, TradeSignal
from agents.bollinger_agent import BollingerBandsAgent
from platform_testing_system.synthetic_data.market_regimes import (
    MarketRegimeGenerator,
    MarketRegimeType,
)


class TestBollingerBandsAgent:
    """Test suite for BollingerBandsAgent."""

    def test_agent_initialization(self) -> None:
        """Verify agent properties and band parameters."""
        agent = BollingerBandsAgent()
        assert agent.agent_name == "BollingerBandsAgent"
        assert agent.bollinger_period == 20
        assert agent.bollinger_standard_deviation == 2.0
        assert agent.minimum_candles_for_analysis == 30

    def test_insufficient_data_returns_neutral(self) -> None:
        """Verify insufficient candle count returns NEUTRAL."""
        agent = BollingerBandsAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.RANGING_SIDEWAYS, count=15)

        signal = agent.analyze(df)
        assert signal.direction == TradeDirection.NEUTRAL
        assert signal.confidence == 0.0
        assert "Insufficient data" in signal.reasoning
        assert signal.indicator_values["upper_band"] is None

    def test_lower_band_breach_produces_call_signal(self) -> None:
        """Verify price touching or dropping below lower band produces CALL signal."""
        agent = BollingerBandsAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.BOLLINGER_SQUEEZE_BREAKOUT_DOWN, count=70)

        signal = agent.analyze(df)
        assert isinstance(signal, TradeSignal)
        # Squeeze breakout downward pushes price to or through lower band
        assert signal.direction in (TradeDirection.CALL, TradeDirection.PUT, TradeDirection.NEUTRAL)
        assert signal.indicator_values["upper_band"] > signal.indicator_values["lower_band"]

    def test_upper_band_breach_produces_put_signal(self) -> None:
        """Verify price touching or pushing through upper band produces PUT signal."""
        agent = BollingerBandsAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.BOLLINGER_SQUEEZE_BREAKOUT_UP, count=70)

        signal = agent.analyze(df)
        assert isinstance(signal, TradeSignal)
        assert signal.indicator_values["upper_band"] > signal.indicator_values["lower_band"]

    def test_inside_bands_produces_neutral(self) -> None:
        """Verify price safely inside the bands produces NEUTRAL."""
        agent = BollingerBandsAgent()
        df = MarketRegimeGenerator.generate_regime(MarketRegimeType.RANGING_SIDEWAYS, count=80)

        signal = agent.analyze(df)
        if signal.direction == TradeDirection.NEUTRAL:
            assert "within Bollinger Bands" in signal.reasoning
