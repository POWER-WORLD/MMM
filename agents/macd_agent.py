"""
Gold Trading Analysis Platform - MACD (Moving Average Convergence Divergence) Agent.

This module implements the MACD technical analysis agent that detects trend
changes through the convergence and divergence of exponential moving averages
in gold price data.

The MACD system uses three components: the MACD line (difference between fast
and slow EMAs), the signal line (EMA of the MACD line), and the histogram
(difference between MACD and signal lines). Crossovers between the MACD and
signal lines generate trading signals.
"""

from typing import Optional

import pandas as pd
import ta

from agents.base_agent import BaseAnalysisAgent, TradeDirection, TradeSignal
from config import PLATFORM_CONFIG


class MovingAverageConvergenceDivergenceAgent(BaseAnalysisAgent):
    """MACD-based technical analysis agent for detecting trend reversals.

    This agent calculates the MACD indicator using configured fast, slow,
    and signal period parameters, then generates trading signals based on
    MACD-signal line crossovers and histogram direction changes.

    Configuration values are sourced from PLATFORM_CONFIG.agent:
        - MACD_FAST_PERIOD: Fast EMA period (default: 12).
        - MACD_SLOW_PERIOD: Slow EMA period (default: 26).
        - MACD_SIGNAL_PERIOD: Signal line EMA period (default: 9).
        - MINIMUM_CANDLES_FOR_ANALYSIS: Minimum data points required (default: 30).
        - MINIMUM_CONFIDENCE_THRESHOLD: Minimum confidence for a signal (default: 0.55).

    Attributes:
        macd_fast_period: Fast EMA period for MACD calculation.
        macd_slow_period: Slow EMA period for MACD calculation.
        macd_signal_period: Signal line EMA smoothing period.
        minimum_candles_for_analysis: Minimum candle count needed for valid analysis.
        minimum_confidence_threshold: Minimum confidence required for a directional signal.
    """

    def __init__(self) -> None:
        """Initialize the Moving Average Convergence Divergence analysis agent.

        Loads all MACD-specific configuration parameters from PLATFORM_CONFIG.agent
        and initializes the base agent with identification details.
        """
        super().__init__(
            agent_name="MovingAverageConvergenceDivergenceAgent",
            agent_description=(
                "Analyzes the MACD (Moving Average Convergence Divergence) indicator "
                "to detect trend changes through MACD-signal line crossovers and "
                "histogram direction, generating CALL signals on bullish crossovers "
                "and PUT signals on bearish crossovers."
            ),
        )
        self.macd_fast_period: int = PLATFORM_CONFIG.agent.MACD_FAST_PERIOD
        self.macd_slow_period: int = PLATFORM_CONFIG.agent.MACD_SLOW_PERIOD
        self.macd_signal_period: int = PLATFORM_CONFIG.agent.MACD_SIGNAL_PERIOD
        self.minimum_candles_for_analysis: int = PLATFORM_CONFIG.agent.MINIMUM_CANDLES_FOR_ANALYSIS
        self.minimum_confidence_threshold: float = PLATFORM_CONFIG.agent.MINIMUM_CONFIDENCE_THRESHOLD

    def analyze(
        self,
        candles_dataframe: pd.DataFrame,
        historical_dataframe: Optional[pd.DataFrame] = None,
    ) -> TradeSignal:
        """Analyze price data using the MACD indicator.

        Calculates MACD line, signal line, and histogram from closing prices,
        then detects crossover events and histogram direction changes to
        determine trade direction and confidence.

        Args:
            candles_dataframe: DataFrame containing OHLCV candle data with
                at least a 'close' column.
            historical_dataframe: Optional DataFrame containing additional
                historical data for extended analysis context.

        Returns:
            A TradeSignal with:
                - CALL direction on bullish MACD-signal crossover.
                - PUT direction on bearish MACD-signal crossover.
                - NEUTRAL direction if no recent crossover detected.
                - Confidence based on histogram magnitude and crossover recency.
                - indicator_values containing macd_line, signal_line, histogram.
        """
        if not self._has_sufficient_data(candles_dataframe, self.minimum_candles_for_analysis):
            self.logger.warning(
                "Insufficient data for MACD analysis. Required: %d, Available: %d",
                self.minimum_candles_for_analysis,
                len(candles_dataframe) if candles_dataframe is not None else 0,
            )
            return self._create_signal(
                direction=TradeDirection.NEUTRAL,
                confidence=0.0,
                reasoning="Insufficient data for MACD analysis.",
                indicator_values={
                    "macd_line": None,
                    "signal_line": None,
                    "histogram": None,
                },
            )

        try:
            macd_indicator = ta.trend.MACD(
                close=candles_dataframe["close"],
                window_slow=self.macd_slow_period,
                window_fast=self.macd_fast_period,
                window_sign=self.macd_signal_period,
            )

            macd_line_series = macd_indicator.macd()
            signal_line_series = macd_indicator.macd_signal()
            histogram_series = macd_indicator.macd_diff()

            current_macd_line = macd_line_series.iloc[-1]
            current_signal_line = signal_line_series.iloc[-1]
            current_histogram = histogram_series.iloc[-1]

            if pd.isna(current_macd_line) or pd.isna(current_signal_line) or pd.isna(current_histogram):
                self.logger.warning("MACD calculation returned NaN values.")
                return self._create_signal(
                    direction=TradeDirection.NEUTRAL,
                    confidence=0.0,
                    reasoning="MACD calculation returned invalid values.",
                    indicator_values={
                        "macd_line": None,
                        "signal_line": None,
                        "histogram": None,
                    },
                )

            indicator_values = {
                "macd_line": round(current_macd_line, 6),
                "signal_line": round(current_signal_line, 6),
                "histogram": round(current_histogram, 6),
            }

            crossover_direction = self._detect_crossover(
                macd_line_series=macd_line_series,
                signal_line_series=signal_line_series,
            )

            histogram_direction = self._analyze_histogram_direction(
                histogram_series=histogram_series,
            )

            if crossover_direction == "bullish":
                histogram_magnitude = abs(current_histogram)
                close_price = candles_dataframe["close"].iloc[-1]
                normalized_magnitude = histogram_magnitude / close_price if close_price != 0 else 0.0

                raw_confidence = min(0.6 + normalized_magnitude * 1000, 0.95)

                if histogram_direction == "increasing":
                    raw_confidence = min(raw_confidence + 0.1, 1.0)

                reasoning = (
                    f"MACD line ({current_macd_line:.6f}) crossed above signal line "
                    f"({current_signal_line:.6f}). Histogram: {current_histogram:.6f}. "
                    f"Histogram direction: {histogram_direction}. "
                    f"Bullish crossover detected, indicating potential upward momentum."
                )

                return self._create_signal(
                    direction=TradeDirection.CALL,
                    confidence=raw_confidence,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

            elif crossover_direction == "bearish":
                histogram_magnitude = abs(current_histogram)
                close_price = candles_dataframe["close"].iloc[-1]
                normalized_magnitude = histogram_magnitude / close_price if close_price != 0 else 0.0

                raw_confidence = min(0.6 + normalized_magnitude * 1000, 0.95)

                if histogram_direction == "decreasing":
                    raw_confidence = min(raw_confidence + 0.1, 1.0)

                reasoning = (
                    f"MACD line ({current_macd_line:.6f}) crossed below signal line "
                    f"({current_signal_line:.6f}). Histogram: {current_histogram:.6f}. "
                    f"Histogram direction: {histogram_direction}. "
                    f"Bearish crossover detected, indicating potential downward momentum."
                )

                return self._create_signal(
                    direction=TradeDirection.PUT,
                    confidence=raw_confidence,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

            else:
                reasoning = (
                    f"No recent MACD-signal line crossover detected. "
                    f"MACD line: {current_macd_line:.6f}, "
                    f"Signal line: {current_signal_line:.6f}, "
                    f"Histogram: {current_histogram:.6f}. "
                    f"Histogram direction: {histogram_direction}."
                )

                return self._create_signal(
                    direction=TradeDirection.NEUTRAL,
                    confidence=0.3,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

        except Exception as analysis_error:
            self.logger.error(
                "Error during MACD analysis: %s", str(analysis_error), exc_info=True
            )
            return self._create_signal(
                direction=TradeDirection.NEUTRAL,
                confidence=0.0,
                reasoning=f"MACD analysis failed due to error: {str(analysis_error)}",
                indicator_values={
                    "macd_line": None,
                    "signal_line": None,
                    "histogram": None,
                },
            )

    def _detect_crossover(
        self,
        macd_line_series: pd.Series,
        signal_line_series: pd.Series,
    ) -> Optional[str]:
        """Detect MACD-signal line crossover events.

        Examines the most recent data points to determine if the MACD line
        has crossed above or below the signal line, indicating a potential
        trend change.

        Args:
            macd_line_series: Series containing MACD line values.
            signal_line_series: Series containing signal line values.

        Returns:
            "bullish" if MACD crossed above signal line,
            "bearish" if MACD crossed below signal line,
            None if no crossover was detected.
        """
        try:
            lookback_window = min(3, len(macd_line_series) - 1)
            if lookback_window < 1:
                return None

            for period_index in range(1, lookback_window + 1):
                current_position = -1
                previous_position = -(period_index + 1)

                if abs(previous_position) > len(macd_line_series):
                    continue

                current_macd = macd_line_series.iloc[current_position]
                previous_macd = macd_line_series.iloc[previous_position]
                current_signal = signal_line_series.iloc[current_position]
                previous_signal = signal_line_series.iloc[previous_position]

                if pd.isna(current_macd) or pd.isna(previous_macd):
                    continue
                if pd.isna(current_signal) or pd.isna(previous_signal):
                    continue

                if previous_macd <= previous_signal and current_macd > current_signal:
                    return "bullish"

                if previous_macd >= previous_signal and current_macd < current_signal:
                    return "bearish"

            return None

        except Exception as crossover_error:
            self.logger.debug(
                "Crossover detection failed: %s", str(crossover_error)
            )
            return None

    def _analyze_histogram_direction(
        self,
        histogram_series: pd.Series,
    ) -> str:
        """Analyze the direction of the MACD histogram.

        Examines recent histogram values to determine if momentum is
        increasing (histogram growing) or decreasing (histogram shrinking).

        Args:
            histogram_series: Series containing MACD histogram values.

        Returns:
            "increasing" if histogram values are growing (bullish momentum),
            "decreasing" if histogram values are shrinking (bearish momentum),
            "flat" if no clear direction is detected.
        """
        try:
            lookback_count = min(3, len(histogram_series))
            if lookback_count < 2:
                return "flat"

            recent_histogram_values = histogram_series.iloc[-lookback_count:]

            if recent_histogram_values.isna().any():
                return "flat"

            consecutive_increases = 0
            consecutive_decreases = 0

            for value_index in range(1, len(recent_histogram_values)):
                current_value = recent_histogram_values.iloc[value_index]
                previous_value = recent_histogram_values.iloc[value_index - 1]

                if current_value > previous_value:
                    consecutive_increases += 1
                elif current_value < previous_value:
                    consecutive_decreases += 1

            if consecutive_increases > consecutive_decreases:
                return "increasing"
            elif consecutive_decreases > consecutive_increases:
                return "decreasing"
            else:
                return "flat"

        except Exception as direction_error:
            self.logger.debug(
                "Histogram direction analysis failed: %s", str(direction_error)
            )
            return "flat"
