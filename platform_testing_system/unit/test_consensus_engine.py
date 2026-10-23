"""
Unit Tests for Consensus Engine (Unanimous 7/7 Agreement Rule).

Verifies signal collection, neutral signal filtering, strict agreement counting,
minimum confidence threshold enforcement, agent crash resilience, and result propagation.
"""

from datetime import datetime
from typing import List
import pandas as pd
import pytest

from agents.base_agent import BaseAnalysisAgent, TradeDirection, TradeSignal
from agents.consensus_engine import ConsensusEngine, ConsensusResult


class MockDeterministicAgent(BaseAnalysisAgent):
    """Mock agent returning deterministic trade signals for testing consensus combinations."""

    def __init__(self, name: str, direction: TradeDirection, confidence: float):
        super().__init__(agent_name=name, agent_description="Mock deterministic agent")
        self._preset_direction = direction
        self._preset_confidence = confidence

    def analyze(self, candles_dataframe: pd.DataFrame, historical_dataframe=None) -> TradeSignal:
        return self._create_signal(
            direction=self._preset_direction,
            confidence=self._preset_confidence,
            reasoning=f"Preset {self._preset_direction.value}",
        )


class MockCrashingAgent(BaseAnalysisAgent):
    """Mock agent designed to raise an unexpected runtime exception."""

    def __init__(self, name: str = "CrashingAgent"):
        super().__init__(agent_name=name, agent_description="Fails unconditionally")

    def analyze(self, candles_dataframe: pd.DataFrame, historical_dataframe=None) -> TradeSignal:
        raise RuntimeError("Simulated agent fatal calculation exception")


class TestConsensusEngine:
    """Test suite for ConsensusEngine."""

    def test_unanimous_7_of_7_agreement_triggers_consensus(self) -> None:
        """Verify 7/7 unanimous CALL signals with confidence >= 0.55 trigger consensus."""
        agents = [
            MockDeterministicAgent(f"Agent_{i}", TradeDirection.CALL, 0.80)
            for i in range(7)
        ]
        engine = ConsensusEngine(agents=agents, required_consensus_count=7)
        df_dummy = pd.DataFrame({"close": [4100.0] * 40})

        result = engine.evaluate_market(df_dummy)
        assert isinstance(result, ConsensusResult)
        assert result.consensus_reached is True
        assert result.direction == TradeDirection.CALL
        assert result.agreeing_agent_count == 7
        assert result.average_confidence == 0.80
        assert len(result.signals) == 7

    def test_partial_agreement_6_of_7_rejects_consensus(self) -> None:
        """Verify 6/7 agreement does NOT reach consensus under strict 7/7 requirement."""
        agents = [
            MockDeterministicAgent(f"Agent_{i}", TradeDirection.CALL, 0.80)
            for i in range(6)
        ]
        # 7th agent is PUT
        agents.append(MockDeterministicAgent("Agent_7", TradeDirection.PUT, 0.70))

        engine = ConsensusEngine(agents=agents, required_consensus_count=7)
        df_dummy = pd.DataFrame({"close": [4100.0] * 40})

        result = engine.evaluate_market(df_dummy)
        assert result.consensus_reached is False
        assert result.direction is None
        assert result.agreeing_agent_count == 6

    def test_neutral_agent_blocks_unanimous_consensus(self) -> None:
        """Verify a single NEUTRAL agent prevents consensus under 7/7 rule."""
        agents = [
            MockDeterministicAgent(f"Agent_{i}", TradeDirection.CALL, 0.85)
            for i in range(6)
        ]
        agents.append(MockDeterministicAgent("Agent_7", TradeDirection.NEUTRAL, 0.0))

        engine = ConsensusEngine(agents=agents, required_consensus_count=7)
        df_dummy = pd.DataFrame({"close": [4100.0] * 40})

        result = engine.evaluate_market(df_dummy)
        assert result.consensus_reached is False
        assert result.agreeing_agent_count == 6

    def test_confidence_threshold_rejection(self) -> None:
        """Verify consensus rejected if 7/7 agree but average confidence < 0.55."""
        agents = [
            MockDeterministicAgent(f"Agent_{i}", TradeDirection.CALL, 0.50)
            for i in range(7)
        ]
        engine = ConsensusEngine(agents=agents, required_consensus_count=7)
        df_dummy = pd.DataFrame({"close": [4100.0] * 40})

        result = engine.evaluate_market(df_dummy)
        # Average confidence is 0.50 which is below PLATFORM_CONFIG.agent.MINIMUM_CONFIDENCE_THRESHOLD (0.55)
        assert result.consensus_reached is False
        assert result.agreeing_agent_count == 7
        assert result.average_confidence == 0.50

    def test_agent_exception_isolation_resilience(self) -> None:
        """Verify that an agent throwing an unhandled exception does not crash consensus engine and yields fallback."""
        agents = [
            MockDeterministicAgent(f"Agent_{i}", TradeDirection.CALL, 0.80)
            for i in range(6)
        ]
        agents.append(MockCrashingAgent("FaultyAgent"))

        engine = ConsensusEngine(agents=agents, required_consensus_count=7)
        df_dummy = pd.DataFrame({"close": [4100.0] * 40})

        # Should execute safely and record 7 signals (with 7th being fallback NEUTRAL)
        result = engine.evaluate_market(df_dummy)
        assert result.consensus_reached is False
        assert len(result.signals) == 7
        fallback = result.signals[-1]
        assert fallback.direction == TradeDirection.NEUTRAL
        assert "Agent failed with error" in fallback.reasoning

    def test_record_trade_result_propagates_to_all_agents(self) -> None:
        """Verify record_trade_result updates accuracy statistics for all registered agents."""
        agents = [
            MockDeterministicAgent(f"Agent_{i}", TradeDirection.CALL, 0.80)
            for i in range(7)
        ]
        engine = ConsensusEngine(agents=agents, required_consensus_count=7)

        engine.record_trade_result(direction=TradeDirection.CALL, was_correct=True)
        stats = engine.get_all_agent_statistics()
        assert len(stats) == 7
        for s in stats:
            assert s["total_predictions"] == 1
            assert s["correct_predictions"] == 1
            assert s["success_rate"] == 100.0
