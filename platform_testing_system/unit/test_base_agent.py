"""
Unit Tests for Base Analysis Agent and Signal Enums.

Verifies abstract base class enforcement, signal clamping, prediction accuracy tracking,
success rate calculation, and TradeDirection enum members.
"""

from datetime import datetime
import pandas as pd
import pytest

from agents.base_agent import BaseAnalysisAgent, TradeDirection, TradeSignal


class ConcreteDummyAgent(BaseAnalysisAgent):
    """Concrete implementation of BaseAnalysisAgent for unit testing."""

    def __init__(self, name: str = "DummyAgent", description: str = "Test dummy"):
        super().__init__(agent_name=name, agent_description=description)

    def analyze(self, candles_dataframe: pd.DataFrame, historical_dataframe=None) -> TradeSignal:
        if not self._has_sufficient_data(candles_dataframe, 10):
            return self._create_signal(TradeDirection.NEUTRAL, 0.0, "Insufficient data")
        return self._create_signal(TradeDirection.CALL, 0.85, "Dummy call signal", {"metric": 100})


class TestBaseAnalysisAgent:
    """Test suite for TradeDirection, TradeSignal, and BaseAnalysisAgent."""

    def test_trade_direction_members(self) -> None:
        """Verify TradeDirection enum members and values."""
        assert TradeDirection.CALL.value == "CALL"
        assert TradeDirection.PUT.value == "PUT"
        assert TradeDirection.NEUTRAL.value == "NEUTRAL"

    def test_trade_signal_dataclass(self) -> None:
        """Verify TradeSignal fields and defaults."""
        now = datetime.now()
        signal = TradeSignal(
            direction=TradeDirection.CALL,
            confidence=0.75,
            agent_name="TestAgent",
            reasoning="Testing signal",
            timestamp=now,
            indicator_values={"key": 42},
        )
        assert signal.direction == TradeDirection.CALL
        assert signal.confidence == 0.75
        assert signal.agent_name == "TestAgent"
        assert signal.reasoning == "Testing signal"
        assert signal.timestamp == now
        assert signal.indicator_values == {"key": 42}

    def test_abstract_class_cannot_be_instantiated_directly(self) -> None:
        """Verify BaseAnalysisAgent cannot be instantiated without implementing analyze."""
        with pytest.raises(TypeError):
            BaseAnalysisAgent("AbstractAgent", "Cannot instantiate")  # type: ignore

    def test_initial_prediction_statistics(self) -> None:
        """Verify fresh agent starts with zeroed counters and 0.0% success rate."""
        agent = ConcreteDummyAgent()
        assert agent.total_predictions == 0
        assert agent.correct_predictions == 0
        assert agent.get_success_rate() == 0.0

        stats = agent.get_statistics()
        assert stats["total_predictions"] == 0
        assert stats["correct_predictions"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["total_call_predictions"] == 0
        assert stats["total_put_predictions"] == 0

    def test_record_prediction_result_tracking(self) -> None:
        """Verify accuracy tracking across CALL and PUT predictions."""
        agent = ConcreteDummyAgent()

        # 2 correct CALLs, 1 incorrect CALL (66.7% win rate)
        agent.record_prediction_result(TradeDirection.CALL, was_correct=True)
        agent.record_prediction_result(TradeDirection.CALL, was_correct=True)
        agent.record_prediction_result(TradeDirection.CALL, was_correct=False)

        assert agent.total_predictions == 3
        assert agent.correct_predictions == 2
        assert agent.total_call_predictions == 3
        assert agent.correct_call_predictions == 2
        assert agent.get_success_rate() == 66.67

        # 1 correct PUT
        agent.record_prediction_result(TradeDirection.PUT, was_correct=True)
        assert agent.total_predictions == 4
        assert agent.correct_predictions == 3
        assert agent.total_put_predictions == 1
        assert agent.correct_put_predictions == 1
        assert agent.get_success_rate() == 75.0

    def test_create_signal_clamps_confidence(self) -> None:
        """Verify _create_signal clamps confidence between 0.0 and 1.0."""
        agent = ConcreteDummyAgent()

        # Over-unity confidence
        sig_high = agent._create_signal(TradeDirection.CALL, 1.45, "Over 100%")
        assert sig_high.confidence == 1.0

        # Negative confidence
        sig_low = agent._create_signal(TradeDirection.PUT, -0.25, "Below 0%")
        assert sig_low.confidence == 0.0

    def test_has_sufficient_data_logic(self) -> None:
        """Verify _has_sufficient_data checks row count and None input."""
        agent = ConcreteDummyAgent()

        assert agent._has_sufficient_data(None, 10) is False
        assert agent._has_sufficient_data(pd.DataFrame(), 10) is False

        df_small = pd.DataFrame({"close": [1, 2, 3]})
        assert agent._has_sufficient_data(df_small, 5) is False
        assert agent._has_sufficient_data(df_small, 3) is True
