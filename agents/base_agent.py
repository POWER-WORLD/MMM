"""
Gold Trading Analysis Platform - Base Analysis Agent.

This module defines the abstract base class for all technical analysis agents,
along with the core data structures used throughout the agent system.

Classes:
    TradeDirection: Enumeration of possible trade directions (CALL, PUT, NEUTRAL).
    TradeSignal: Dataclass representing a trading signal produced by an agent.
    BaseAnalysisAgent: Abstract base class providing the common interface and
        tracking functionality for all technical analysis agents.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

import logging

import pandas as pd


class TradeDirection(Enum):
    """Enumeration of possible trade directions.

    Attributes:
        CALL: Bullish signal indicating expected price increase.
        PUT: Bearish signal indicating expected price decrease.
        NEUTRAL: No clear directional bias detected.
    """

    CALL = "CALL"
    PUT = "PUT"
    NEUTRAL = "NEUTRAL"


@dataclass
class TradeSignal:
    """Represents a trading signal produced by an analysis agent.

    Attributes:
        direction: The recommended trade direction (CALL, PUT, or NEUTRAL).
        confidence: Confidence level of the signal, ranging from 0.0 to 1.0.
        agent_name: Name of the agent that generated this signal.
        reasoning: Human-readable explanation of why this signal was generated.
        timestamp: The datetime when this signal was created.
        indicator_values: Dictionary containing the raw indicator values
            used to generate this signal.
    """

    direction: TradeDirection
    confidence: float
    agent_name: str
    reasoning: str
    timestamp: datetime
    indicator_values: dict = field(default_factory=dict)


class BaseAnalysisAgent(ABC):
    """Abstract base class for all technical analysis agents.

    Provides the common interface for analyzing price data and generating
    trade signals, as well as tracking prediction accuracy over time.

    Each concrete agent implements a specific technical analysis strategy
    and produces signals based on its indicator calculations.

    Attributes:
        agent_name: Unique identifier name for this agent.
        agent_description: Human-readable description of the agent's strategy.
        total_predictions: Total number of predictions made.
        correct_predictions: Number of predictions that were correct.
        total_call_predictions: Total number of CALL predictions made.
        total_put_predictions: Total number of PUT predictions made.
        correct_call_predictions: Number of correct CALL predictions.
        correct_put_predictions: Number of correct PUT predictions.
        logger: Logger instance for this agent.
    """

    def __init__(self, agent_name: str, agent_description: str) -> None:
        """Initialize the base analysis agent.

        Args:
            agent_name: Unique identifier name for this agent.
            agent_description: Human-readable description of the agent's
                analysis strategy and methodology.
        """
        self.agent_name = agent_name
        self.agent_description = agent_description
        self.total_predictions: int = 0
        self.correct_predictions: int = 0
        self.total_call_predictions: int = 0
        self.total_put_predictions: int = 0
        self.correct_call_predictions: int = 0
        self.correct_put_predictions: int = 0
        self.logger = logging.getLogger(f"agent.{agent_name}")

    @abstractmethod
    def analyze(
        self,
        candles_dataframe: pd.DataFrame,
        historical_dataframe: Optional[pd.DataFrame] = None,
    ) -> TradeSignal:
        """Analyze price data and return a trade signal.

        Args:
            candles_dataframe: DataFrame containing OHLCV candle data with
                columns: open, high, low, close, volume.
            historical_dataframe: Optional DataFrame containing additional
                historical data for extended analysis context.

        Returns:
            A TradeSignal containing the analysis result, confidence level,
            reasoning, and raw indicator values.
        """
        pass

    def get_success_rate(self) -> float:
        """Calculate overall success rate as a percentage.

        Returns:
            The success rate as a percentage (0.0 to 100.0), rounded to
            two decimal places. Returns 0.0 if no predictions have been made.
        """
        if self.total_predictions == 0:
            return 0.0
        return round(self.correct_predictions / self.total_predictions * 100, 2)

    def record_prediction_result(
        self, direction: TradeDirection, was_correct: bool
    ) -> None:
        """Record the result of a prediction for accuracy tracking.

        Updates the internal counters for total and correct predictions,
        broken down by trade direction.

        Args:
            direction: The direction of the prediction that was evaluated.
            was_correct: Whether the prediction turned out to be correct.
        """
        self.total_predictions += 1
        if was_correct:
            self.correct_predictions += 1
        if direction == TradeDirection.CALL:
            self.total_call_predictions += 1
            if was_correct:
                self.correct_call_predictions += 1
        elif direction == TradeDirection.PUT:
            self.total_put_predictions += 1
            if was_correct:
                self.correct_put_predictions += 1

    def get_statistics(self) -> dict:
        """Return comprehensive statistics for this agent.

        Returns:
            A dictionary containing all prediction tracking statistics
            including agent identification, total counts, correct counts,
            and success rate percentage.
        """
        return {
            "agent_name": self.agent_name,
            "agent_description": self.agent_description,
            "total_predictions": self.total_predictions,
            "correct_predictions": self.correct_predictions,
            "success_rate": self.get_success_rate(),
            "total_call_predictions": self.total_call_predictions,
            "correct_call_predictions": self.correct_call_predictions,
            "total_put_predictions": self.total_put_predictions,
            "correct_put_predictions": self.correct_put_predictions,
        }

    def _create_signal(
        self,
        direction: TradeDirection,
        confidence: float,
        reasoning: str,
        indicator_values: dict = None,
    ) -> TradeSignal:
        """Helper to create a properly formatted TradeSignal.

        Clamps the confidence value to the valid range [0.0, 1.0] and
        populates the signal with the agent's name and current timestamp.

        Args:
            direction: The recommended trade direction.
            confidence: Raw confidence value (will be clamped to 0.0-1.0).
            reasoning: Human-readable explanation of the signal.
            indicator_values: Optional dictionary of raw indicator values.

        Returns:
            A fully populated TradeSignal instance.
        """
        return TradeSignal(
            direction=direction,
            confidence=min(max(confidence, 0.0), 1.0),
            agent_name=self.agent_name,
            reasoning=reasoning,
            timestamp=datetime.now(),
            indicator_values=indicator_values or {},
        )

    def _has_sufficient_data(self, dataframe: pd.DataFrame, minimum_rows: int) -> bool:
        """Check if dataframe has enough data for analysis.

        Args:
            dataframe: The DataFrame to check for sufficient row count.
            minimum_rows: The minimum number of rows required for analysis.

        Returns:
            True if the dataframe is not None and contains at least
            minimum_rows rows, False otherwise.
        """
        return dataframe is not None and len(dataframe) >= minimum_rows
