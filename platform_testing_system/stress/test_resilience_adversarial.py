"""
Adversarial Data Resilience and Fault Tolerance Tests.

Injects corrupt, malformed, missing, infinite, and anomalous data into all
7 analysis agents and the ConsensusEngine to verify fault isolation and zero crash guarantees.
"""

from typing import List
import pytest

from agents.adx_agent import AverageDirectionalIndexAgent
from agents.base_agent import BaseAnalysisAgent, TradeDirection, TradeSignal
from agents.bollinger_agent import BollingerBandsAgent
from agents.consensus_engine import ConsensusEngine
from agents.ema_crossover_agent import ExponentialMovingAverageCrossoverAgent
from agents.ichimoku_agent import IchimokuCloudAgent
from agents.macd_agent import MovingAverageConvergenceDivergenceAgent
from agents.rsi_agent import RelativeStrengthIndexAgent
from agents.stochastic_agent import StochasticOscillatorAgent
from platform_testing_system.synthetic_data.anomaly_generator import (
    AnomalyDataGenerator,
    AnomalyType,
)


class TestResilienceAdversarial:
    """Fault tolerance suite for adversarial data conditions."""

    @pytest.fixture
    def all_agents(self) -> List[BaseAnalysisAgent]:
        """Fresh list of all 7 analysis agents."""
        return [
            RelativeStrengthIndexAgent(),
            MovingAverageConvergenceDivergenceAgent(),
            BollingerBandsAgent(),
            ExponentialMovingAverageCrossoverAgent(),
            StochasticOscillatorAgent(),
            AverageDirectionalIndexAgent(),
            IchimokuCloudAgent(),
        ]

    @pytest.mark.parametrize("anomaly_type", [
        AnomalyType.EMPTY_DATAFRAME,
        AnomalyType.SINGLE_ROW_DATAFRAME,
        AnomalyType.INSUFFICIENT_ROWS,
        AnomalyType.MISSING_CLOSE_COLUMN,
        AnomalyType.MISSING_ALL_PRICE_COLUMNS,
        AnomalyType.ALL_NAN_VALUES,
        AnomalyType.INTERMITTENT_NANS,
        AnomalyType.ZERO_PRICES,
        AnomalyType.NEGATIVE_PRICES,
        AnomalyType.INVERTED_HIGH_LOW,
        AnomalyType.EXTREME_SPIKE_OUTLIER,
        AnomalyType.DUPLICATE_TIMESTAMPS,
        AnomalyType.NON_CHRONOLOGICAL_TIMESTAMPS,
        AnomalyType.ZERO_VOLUME,
        AnomalyType.INFINITE_VALUES,
    ])
    def test_agents_resilience_under_adversarial_input(self, all_agents, anomaly_type) -> None:
        """
        Verify that NO agent crashes or raises unhandled exceptions when presented
        with corrupted, missing, or adversarial datasets.
        """
        corrupted_df = AnomalyDataGenerator.generate_anomaly(anomaly_type, count=50)

        for agent in all_agents:
            signal = agent.analyze(corrupted_df)
            assert isinstance(signal, TradeSignal), f"Agent {agent.agent_name} failed on {anomaly_type}"
            assert signal.direction in (TradeDirection.CALL, TradeDirection.PUT, TradeDirection.NEUTRAL)
            assert 0.0 <= signal.confidence <= 1.0

    @pytest.mark.parametrize("anomaly_type", [
        AnomalyType.EMPTY_DATAFRAME,
        AnomalyType.ALL_NAN_VALUES,
        AnomalyType.MISSING_CLOSE_COLUMN,
        AnomalyType.EXTREME_SPIKE_OUTLIER,
    ])
    def test_consensus_engine_resilience_under_adversarial_input(self, all_agents, anomaly_type) -> None:
        """Verify ConsensusEngine processes adversarial inputs gracefully and rejects consensus."""
        engine = ConsensusEngine(agents=all_agents, required_consensus_count=7)
        corrupted_df = AnomalyDataGenerator.generate_anomaly(anomaly_type, count=50)

        result = engine.evaluate_market(corrupted_df)
        assert result is not None
        assert result.consensus_reached is False
        assert len(result.signals) == 7
