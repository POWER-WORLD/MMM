"""
Gold Trading Analysis Platform - Consensus Engine.

This module implements the Consensus Engine that aggregates trading signals
from all seven technical analysis agents to reach a unified trading decision.

The engine collects signals from each agent, filters out neutral signals,
checks if the required number of agents agree on a direction, and verifies
that the average confidence meets the minimum threshold. Only when consensus
is achieved with sufficient confidence does the engine recommend a trade.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import logging

import pandas as pd

from agents.base_agent import BaseAnalysisAgent, TradeDirection, TradeSignal
from config import PLATFORM_CONFIG


@dataclass
class ConsensusResult:
    """Represents the result of consensus evaluation across all agents.

    Attributes:
        consensus_reached: Whether sufficient agreement was achieved among agents.
        direction: The agreed-upon trade direction, or None if no consensus.
        signals: List of all individual TradeSignal objects from each agent.
        average_confidence: The average confidence of agents agreeing on direction.
        agreeing_agent_count: Number of non-neutral agents agreeing on direction.
        timestamp: The datetime when this consensus was evaluated.
    """

    consensus_reached: bool
    direction: Optional[TradeDirection]
    signals: List[TradeSignal]
    average_confidence: float
    agreeing_agent_count: int
    timestamp: datetime


class ConsensusEngine:
    """Aggregates signals from all technical analysis agents for consensus decisions.

    The Consensus Engine manages a collection of analysis agents, collects
    their individual signals for given market data, and determines whether
    sufficient agreement exists to recommend a trade. It also tracks prediction
    results for all agents and provides comprehensive statistics.

    The consensus process:
        1. Collect signals from all registered agents.
        2. Filter out NEUTRAL signals.
        3. Count agreements for each direction (CALL vs PUT).
        4. Check if the required number of agents agree on the same direction.
        5. Verify that the average confidence of agreeing agents meets the
           minimum confidence threshold.
        6. Only reach consensus if both conditions are satisfied.

    Configuration values are sourced from PLATFORM_CONFIG.agent:
        - REQUIRED_CONSENSUS_COUNT: Minimum agents that must agree (default: 7).
        - MINIMUM_CONFIDENCE_THRESHOLD: Minimum average confidence (default: 0.55).

    Attributes:
        analysis_agents: List of all registered analysis agents.
        required_consensus_count: Minimum number of agents that must agree.
        minimum_confidence_threshold: Minimum average confidence for consensus.
        logger: Logger instance for consensus operations.
    """

    def __init__(
        self,
        agents: List[BaseAnalysisAgent],
        required_consensus_count: int,
    ) -> None:
        """Initialize the Consensus Engine with registered agents.

        Args:
            agents: List of BaseAnalysisAgent instances to collect signals from.
            required_consensus_count: The minimum number of non-neutral agents
                that must agree on the same direction for consensus.
        """
        self.analysis_agents: List[BaseAnalysisAgent] = agents
        self.required_consensus_count: int = required_consensus_count
        self.minimum_confidence_threshold: float = PLATFORM_CONFIG.agent.MINIMUM_CONFIDENCE_THRESHOLD
        self.logger = logging.getLogger("consensus_engine")

        self.logger.info(
            "ConsensusEngine initialized with %d agents. Required consensus count: %d. "
            "Minimum confidence threshold: %.2f.",
            len(self.analysis_agents),
            self.required_consensus_count,
            self.minimum_confidence_threshold,
        )

    def evaluate_market(
        self,
        candles_dataframe: pd.DataFrame,
        historical_dataframe: Optional[pd.DataFrame] = None,
    ) -> ConsensusResult:
        """Evaluate market conditions by collecting and aggregating agent signals.

        Runs analysis on all registered agents, collects their trading signals,
        and determines whether consensus has been reached based on the required
        agreement count and minimum confidence threshold.

        Args:
            candles_dataframe: DataFrame containing OHLCV candle data to be
                analyzed by all agents.
            historical_dataframe: Optional DataFrame containing additional
                historical data passed to agents for extended analysis.

        Returns:
            A ConsensusResult containing:
                - Whether consensus was reached.
                - The agreed-upon direction (if consensus reached).
                - All individual agent signals.
                - Average confidence of agreeing agents.
                - Count of agents agreeing on the dominant direction.
        """
        self.logger.info("Beginning market evaluation across %d agents.", len(self.analysis_agents))

        collected_signals: List[TradeSignal] = []

        for analysis_agent in self.analysis_agents:
            try:
                agent_signal = analysis_agent.analyze(
                    candles_dataframe=candles_dataframe,
                    historical_dataframe=historical_dataframe,
                )
                collected_signals.append(agent_signal)

                self.logger.debug(
                    "Agent '%s' signal: direction=%s, confidence=%.4f, reasoning='%s'",
                    agent_signal.agent_name,
                    agent_signal.direction.value,
                    agent_signal.confidence,
                    agent_signal.reasoning[:100],
                )

            except Exception as agent_error:
                self.logger.error(
                    "Agent '%s' failed during analysis: %s",
                    analysis_agent.agent_name,
                    str(agent_error),
                    exc_info=True,
                )
                fallback_signal = TradeSignal(
                    direction=TradeDirection.NEUTRAL,
                    confidence=0.0,
                    agent_name=analysis_agent.agent_name,
                    reasoning=f"Agent failed with error: {str(agent_error)}",
                    timestamp=datetime.now(),
                    indicator_values={},
                )
                collected_signals.append(fallback_signal)

        non_neutral_signals = [
            signal for signal in collected_signals
            if signal.direction != TradeDirection.NEUTRAL
        ]

        if not non_neutral_signals:
            self.logger.info("No non-neutral signals from any agent. No consensus reached.")
            return ConsensusResult(
                consensus_reached=False,
                direction=None,
                signals=collected_signals,
                average_confidence=0.0,
                agreeing_agent_count=0,
                timestamp=datetime.now(),
            )

        call_signals = [
            signal for signal in non_neutral_signals
            if signal.direction == TradeDirection.CALL
        ]
        put_signals = [
            signal for signal in non_neutral_signals
            if signal.direction == TradeDirection.PUT
        ]

        call_count = len(call_signals)
        put_count = len(put_signals)

        self.logger.info(
            "Signal tally - CALL: %d, PUT: %d, NEUTRAL: %d (of %d total agents).",
            call_count,
            put_count,
            len(collected_signals) - len(non_neutral_signals),
            len(collected_signals),
        )

        if call_count >= put_count:
            dominant_direction = TradeDirection.CALL
            dominant_signals = call_signals
            dominant_count = call_count
        else:
            dominant_direction = TradeDirection.PUT
            dominant_signals = put_signals
            dominant_count = put_count

        average_confidence_of_dominant = (
            sum(signal.confidence for signal in dominant_signals) / len(dominant_signals)
            if dominant_signals
            else 0.0
        )

        has_sufficient_agreement = dominant_count >= self.required_consensus_count
        has_sufficient_confidence = average_confidence_of_dominant >= self.minimum_confidence_threshold

        consensus_reached = has_sufficient_agreement and has_sufficient_confidence

        if consensus_reached:
            self.logger.info(
                "CONSENSUS REACHED: direction=%s, agreeing_agents=%d/%d, "
                "average_confidence=%.4f (threshold=%.2f).",
                dominant_direction.value,
                dominant_count,
                len(self.analysis_agents),
                average_confidence_of_dominant,
                self.minimum_confidence_threshold,
            )
        else:
            reasons = []
            if not has_sufficient_agreement:
                reasons.append(
                    f"insufficient agreement ({dominant_count}/{self.required_consensus_count} required)"
                )
            if not has_sufficient_confidence:
                reasons.append(
                    f"insufficient confidence ({average_confidence_of_dominant:.4f}/{self.minimum_confidence_threshold:.2f} required)"
                )
            self.logger.info(
                "NO CONSENSUS: dominant_direction=%s, reason(s): %s.",
                dominant_direction.value,
                "; ".join(reasons),
            )

        return ConsensusResult(
            consensus_reached=consensus_reached,
            direction=dominant_direction if consensus_reached else None,
            signals=collected_signals,
            average_confidence=round(average_confidence_of_dominant, 4),
            agreeing_agent_count=dominant_count,
            timestamp=datetime.now(),
        )

    def get_all_agent_statistics(self) -> List[dict]:
        """Retrieve comprehensive statistics for all registered agents.

        Returns:
            A list of dictionaries, each containing the prediction tracking
            statistics for one agent, including agent name, total predictions,
            correct predictions, success rate, and direction-specific counts.
        """
        all_statistics: List[dict] = []

        for analysis_agent in self.analysis_agents:
            agent_statistics = analysis_agent.get_statistics()
            all_statistics.append(agent_statistics)
            self.logger.debug(
                "Agent '%s' statistics: %s",
                analysis_agent.agent_name,
                agent_statistics,
            )

        return all_statistics

    def record_trade_result(
        self,
        direction: TradeDirection,
        was_correct: bool,
    ) -> None:
        """Record a trade result for all agents that predicted the given direction.

        Iterates through all registered agents and updates the prediction
        tracking for those whose most recent signal matches the specified
        direction. This allows tracking of each agent's accuracy over time.

        Args:
            direction: The direction of the trade that was evaluated.
            was_correct: Whether the trade turned out to be correct.
        """
        self.logger.info(
            "Recording trade result: direction=%s, was_correct=%s.",
            direction.value,
            was_correct,
        )

        for analysis_agent in self.analysis_agents:
            analysis_agent.record_prediction_result(
                direction=direction,
                was_correct=was_correct,
            )
            self.logger.debug(
                "Recorded result for agent '%s': direction=%s, was_correct=%s. "
                "New success rate: %.2f%%.",
                analysis_agent.agent_name,
                direction.value,
                was_correct,
                analysis_agent.get_success_rate(),
            )
