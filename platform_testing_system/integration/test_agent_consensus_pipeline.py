"""
Integration Tests for Multi-Agent Analysis and Consensus Engine Pipeline.

Verifies that all 7 specialized agents analyze synthetic market regimes concurrently
and that the Consensus Engine aggregates individual signals into unanimous trading decisions.
"""

from typing import List
import pytest

from agents.adx_agent import AverageDirectionalIndexAgent
from agents.base_agent import BaseAnalysisAgent, TradeDirection, TradeSignal
from agents.bollinger_agent import BollingerBandsAgent
from agents.consensus_engine import ConsensusEngine, ConsensusResult
from agents.ema_crossover_agent import ExponentialMovingAverageCrossoverAgent
from agents.ichimoku_agent import IchimokuCloudAgent
from agents.macd_agent import MovingAverageConvergenceDivergenceAgent
from agents.rsi_agent import RelativeStrengthIndexAgent
from agents.stochastic_agent import StochasticOscillatorAgent
from platform_testing_system.synthetic_data.market_regimes import (
    MarketRegimeGenerator,
    MarketRegimeType,
)


class TestAgentConsensusPipeline:
    """Pipeline integration test: Market Data -> 7 Technical Agents -> Consensus Engine."""

    @pytest.fixture
    def consensus_system(self):
        """Instantiate all 7 agents and consensus engine."""
        agents: List[BaseAnalysisAgent] = [
            RelativeStrengthIndexAgent(),
            MovingAverageConvergenceDivergenceAgent(),
            BollingerBandsAgent(),
            ExponentialMovingAverageCrossoverAgent(),
            StochasticOscillatorAgent(),
            AverageDirectionalIndexAgent(),
            IchimokuCloudAgent(),
        ]
        engine = ConsensusEngine(agents=agents, required_consensus_count=7)
        return agents, engine

    def test_all_seven_agents_evaluate_bull_trend(self, consensus_system) -> None:
        """Verify all 7 agents execute without exceptions on bull trend data."""
        agents, engine = consensus_system
        candles_df = MarketRegimeGenerator.generate_regime(MarketRegimeType.BULL_TREND, count=120)

        result: ConsensusResult = engine.evaluate_market(candles_dataframe=candles_df)
        assert len(result.signals) == 7

        for signal in result.signals:
            assert isinstance(signal, TradeSignal)
            assert signal.direction in (TradeDirection.CALL, TradeDirection.PUT, TradeDirection.NEUTRAL)
            assert 0.0 <= signal.confidence <= 1.0
            assert len(signal.reasoning) > 0
            assert signal.timestamp is not None

    def test_ranging_market_yields_no_consensus(self, consensus_system) -> None:
        """Verify ranging choppy market does NOT reach unanimous consensus."""
        agents, engine = consensus_system
        candles_df = MarketRegimeGenerator.generate_regime(MarketRegimeType.RANGING_SIDEWAYS, count=120)

        result: ConsensusResult = engine.evaluate_market(candles_dataframe=candles_df)
        assert result.consensus_reached is False

    def test_unanimous_call_consensus_triggers_execution_recommendation(self) -> None:
        """
        Verify that when all 7 agents agree on CALL with confidence >= 0.55,
        the consensus engine produces consensus_reached=True with TradeDirection.CALL.
        """
        class DeterministicBullAgent(RelativeStrengthIndexAgent):
            def __init__(self, name: str):
                super().__init__()
                self.agent_name = name

            def analyze(self, candles_dataframe, historical_dataframe=None):
                return TradeSignal(
                    direction=TradeDirection.CALL,
                    confidence=0.88,
                    agent_name=self.agent_name,
                    reasoning="Strong institutional bullish confluence",
                    timestamp=None,
                )

        unanimous_agents = [DeterministicBullAgent(f"Agent_{i}") for i in range(7)]
        engine = ConsensusEngine(agents=unanimous_agents, required_consensus_count=7)

        candles_df = MarketRegimeGenerator.generate_regime(MarketRegimeType.BULL_TREND, count=100)
        result = engine.evaluate_market(candles_dataframe=candles_df)

        assert result.consensus_reached is True
        assert result.direction == TradeDirection.CALL
        assert result.agreeing_agent_count == 7
        assert result.average_confidence >= 0.80

    def test_unanimous_put_consensus_triggers_execution_recommendation(self) -> None:
        """
        Verify that when all 7 agents agree on PUT with confidence >= 0.55,
        the consensus engine produces consensus_reached=True with TradeDirection.PUT.
        """
        class DeterministicBearAgent(RelativeStrengthIndexAgent):
            def __init__(self, name: str):
                super().__init__()
                self.agent_name = name

            def analyze(self, candles_dataframe, historical_dataframe=None):
                return TradeSignal(
                    direction=TradeDirection.PUT,
                    confidence=0.84,
                    agent_name=self.agent_name,
                    reasoning="Strong institutional bearish breakdown",
                    timestamp=None,
                )

        unanimous_agents = [DeterministicBearAgent(f"Agent_{i}") for i in range(7)]
        engine = ConsensusEngine(agents=unanimous_agents, required_consensus_count=7)

        candles_df = MarketRegimeGenerator.generate_regime(MarketRegimeType.BEAR_TREND, count=100)
        result = engine.evaluate_market(candles_dataframe=candles_df)

        assert result.consensus_reached is True
        assert result.direction == TradeDirection.PUT
        assert result.agreeing_agent_count == 7
        assert result.average_confidence >= 0.80
