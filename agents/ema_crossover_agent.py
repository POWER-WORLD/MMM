"""
Gold Trading Analysis Platform - EMA (Exponential Moving Average) Crossover Agent.

This module implements the EMA Crossover technical analysis agent that detects
trend changes through the crossover of short-period and long-period exponential
moving averages in gold price data.

The EMA crossover strategy uses two EMAs of different periods. When the shorter
EMA crosses above the longer EMA, it generates a bullish signal (CALL). When
the shorter EMA crosses below the longer EMA, it generates a bearish signal (PUT).
The speed and angle of the crossover contribute to signal confidence.
"""

from typing import Optional

import pandas as pd
import ta

from agents.base_agent import BaseAnalysisAgent, TradeDirection, TradeSignal
from config import PLATFORM_CONFIG


class ExponentialMovingAverageCrossoverAgent(BaseAnalysisAgent):
    """EMA Crossover technical analysis agent for detecting trend changes.

    This agent calculates short-period and long-period Exponential Moving
    Averages, then generates trading signals based on crossover events between
    the two EMAs. Signal confidence is derived from the crossover angle/speed
    and the distance between the two EMAs.

    Configuration values are sourced from PLATFORM_CONFIG.agent:
        - EMA_SHORT_PERIOD: Short EMA period (default: 9).
        - EMA_LONG_PERIOD: Long EMA period (default: 21).
        - MINIMUM_CANDLES_FOR_ANALYSIS: Minimum data points required (default: 30).
        - MINIMUM_CONFIDENCE_THRESHOLD: Minimum confidence for a signal (default: 0.55).

    Attributes:
        ema_short_period: Short-term EMA period.
        ema_long_period: Long-term EMA period.
        minimum_candles_for_analysis: Minimum candle count needed for valid analysis.
        minimum_confidence_threshold: Minimum confidence required for a directional signal.
    """

    def __init__(self) -> None:
        """Initialize the Exponential Moving Average Crossover analysis agent.

        Loads all EMA-specific configuration parameters from PLATFORM_CONFIG.agent
        and initializes the base agent with identification details.
        """
        super().__init__(
            agent_name="ExponentialMovingAverageCrossoverAgent",
            agent_description=(
                "Analyzes EMA (Exponential Moving Average) crossovers between "
                "short-period and long-period EMAs to detect trend changes, "
                "generating CALL signals on bullish crossovers and PUT signals "
                "on bearish crossovers with confidence based on crossover dynamics."
            ),
        )
        self.ema_short_period: int = PLATFORM_CONFIG.agent.EMA_SHORT_PERIOD
        self.ema_long_period: int = PLATFORM_CONFIG.agent.EMA_LONG_PERIOD
        self.minimum_candles_for_analysis: int = PLATFORM_CONFIG.agent.MINIMUM_CANDLES_FOR_ANALYSIS
        self.minimum_confidence_threshold: float = PLATFORM_CONFIG.agent.MINIMUM_CONFIDENCE_THRESHOLD

    def analyze(
        self,
        candles_dataframe: pd.DataFrame,
        historical_dataframe: Optional[pd.DataFrame] = None,
    ) -> TradeSignal:
        """Analyze price data using EMA crossover strategy.

        Calculates short and long EMAs from closing prices, then detects
        crossover events and measures the speed/angle of crossover to
        determine trade direction and confidence level.

        Args:
            candles_dataframe: DataFrame containing OHLCV candle data with
                at least a 'close' column.
            historical_dataframe: Optional DataFrame containing additional
                historical data for extended analysis context.

        Returns:
            A TradeSignal with:
                - CALL direction on bullish EMA crossover (short above long).
                - PUT direction on bearish EMA crossover (short below long).
                - NEUTRAL direction if no recent crossover detected.
                - Confidence based on crossover speed and EMA distance.
                - indicator_values containing ema_short, ema_long,
                  and crossover_distance.
        """
        if not self._has_sufficient_data(candles_dataframe, self.minimum_candles_for_analysis):
            self.logger.warning(
                "Insufficient data for EMA Crossover analysis. Required: %d, Available: %d",
                self.minimum_candles_for_analysis,
                len(candles_dataframe) if candles_dataframe is not None else 0,
            )
            return self._create_signal(
                direction=TradeDirection.NEUTRAL,
                confidence=0.0,
                reasoning="Insufficient data for EMA Crossover analysis.",
                indicator_values={
                    "ema_short": None,
                    "ema_long": None,
                    "crossover_distance": None,
                },
            )

        try:
            short_ema_indicator = ta.trend.EMAIndicator(
                close=candles_dataframe["close"],
                window=self.ema_short_period,
            )
            long_ema_indicator = ta.trend.EMAIndicator(
                close=candles_dataframe["close"],
                window=self.ema_long_period,
            )

            short_ema_series = short_ema_indicator.ema_indicator()
            long_ema_series = long_ema_indicator.ema_indicator()

            current_short_ema = short_ema_series.iloc[-1]
            current_long_ema = long_ema_series.iloc[-1]

            if pd.isna(current_short_ema) or pd.isna(current_long_ema):
                self.logger.warning("EMA calculation returned NaN values.")
                return self._create_signal(
                    direction=TradeDirection.NEUTRAL,
                    confidence=0.0,
                    reasoning="EMA calculation returned invalid values.",
                    indicator_values={
                        "ema_short": None,
                        "ema_long": None,
                        "crossover_distance": None,
                    },
                )

            crossover_distance = current_short_ema - current_long_ema

            indicator_values = {
                "ema_short": round(current_short_ema, 4),
                "ema_long": round(current_long_ema, 4),
                "crossover_distance": round(crossover_distance, 4),
            }

            crossover_type = self._detect_ema_crossover(
                short_ema_series=short_ema_series,
                long_ema_series=long_ema_series,
            )

            crossover_speed = self._calculate_crossover_speed(
                short_ema_series=short_ema_series,
                long_ema_series=long_ema_series,
            )

            if crossover_type == "bullish":
                close_price = candles_dataframe["close"].iloc[-1]
                normalized_distance = abs(crossover_distance) / close_price if close_price != 0 else 0.0
                raw_confidence = min(0.6 + normalized_distance * 500 + crossover_speed * 0.2, 0.95)

                reasoning = (
                    f"Short EMA ({self.ema_short_period}) at {current_short_ema:.4f} "
                    f"crossed above Long EMA ({self.ema_long_period}) at {current_long_ema:.4f}. "
                    f"Crossover distance: {crossover_distance:.4f}. "
                    f"Crossover speed factor: {crossover_speed:.4f}. "
                    f"Bullish crossover indicates potential upward trend."
                )

                return self._create_signal(
                    direction=TradeDirection.CALL,
                    confidence=raw_confidence,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

            elif crossover_type == "bearish":
                close_price = candles_dataframe["close"].iloc[-1]
                normalized_distance = abs(crossover_distance) / close_price if close_price != 0 else 0.0
                raw_confidence = min(0.6 + normalized_distance * 500 + crossover_speed * 0.2, 0.95)

                reasoning = (
                    f"Short EMA ({self.ema_short_period}) at {current_short_ema:.4f} "
                    f"crossed below Long EMA ({self.ema_long_period}) at {current_long_ema:.4f}. "
                    f"Crossover distance: {crossover_distance:.4f}. "
                    f"Crossover speed factor: {crossover_speed:.4f}. "
                    f"Bearish crossover indicates potential downward trend."
                )

                return self._create_signal(
                    direction=TradeDirection.PUT,
                    confidence=raw_confidence,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

            else:
                if current_short_ema > current_long_ema:
                    trend_description = "bullish (short EMA above long EMA)"
                elif current_short_ema < current_long_ema:
                    trend_description = "bearish (short EMA below long EMA)"
                else:
                    trend_description = "flat (EMAs converged)"

                reasoning = (
                    f"No recent EMA crossover detected. Current trend is {trend_description}. "
                    f"Short EMA ({self.ema_short_period}): {current_short_ema:.4f}, "
                    f"Long EMA ({self.ema_long_period}): {current_long_ema:.4f}. "
                    f"Crossover distance: {crossover_distance:.4f}."
                )

                return self._create_signal(
                    direction=TradeDirection.NEUTRAL,
                    confidence=0.3,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

        except Exception as analysis_error:
            self.logger.error(
                "Error during EMA Crossover analysis: %s",
                str(analysis_error),
                exc_info=True,
            )
            return self._create_signal(
                direction=TradeDirection.NEUTRAL,
                confidence=0.0,
                reasoning=f"EMA Crossover analysis failed due to error: {str(analysis_error)}",
                indicator_values={
                    "ema_short": None,
                    "ema_long": None,
                    "crossover_distance": None,
                },
            )

    def _detect_ema_crossover(
        self,
        short_ema_series: pd.Series,
        long_ema_series: pd.Series,
    ) -> Optional[str]:
        """Detect EMA crossover events in recent price data.

        Examines the most recent data points to determine if the short EMA
        has crossed above or below the long EMA, indicating a potential
        trend change.

        Args:
            short_ema_series: Series containing short-period EMA values.
            long_ema_series: Series containing long-period EMA values.

        Returns:
            "bullish" if short EMA crossed above long EMA,
            "bearish" if short EMA crossed below long EMA,
            None if no crossover was detected.
        """
        try:
            lookback_window = min(3, len(short_ema_series) - 1)
            if lookback_window < 1:
                return None

            for period_index in range(1, lookback_window + 1):
                current_position = -1
                previous_position = -(period_index + 1)

                if abs(previous_position) > len(short_ema_series):
                    continue

                current_short = short_ema_series.iloc[current_position]
                previous_short = short_ema_series.iloc[previous_position]
                current_long = long_ema_series.iloc[current_position]
                previous_long = long_ema_series.iloc[previous_position]

                if any(pd.isna(value) for value in [current_short, previous_short, current_long, previous_long]):
                    continue

                if previous_short <= previous_long and current_short > current_long:
                    return "bullish"

                if previous_short >= previous_long and current_short < current_long:
                    return "bearish"

            return None

        except Exception as crossover_error:
            self.logger.debug(
                "EMA crossover detection failed: %s", str(crossover_error)
            )
            return None

    def _calculate_crossover_speed(
        self,
        short_ema_series: pd.Series,
        long_ema_series: pd.Series,
    ) -> float:
        """Calculate the speed/angle of the EMA crossover.

        Measures how quickly the short EMA is diverging from the long EMA
        over the most recent data points. A faster divergence indicates
        stronger momentum and higher confidence.

        Args:
            short_ema_series: Series containing short-period EMA values.
            long_ema_series: Series containing long-period EMA values.

        Returns:
            A normalized speed factor between 0.0 and 1.0, where higher
            values indicate faster EMA divergence.
        """
        try:
            lookback_count = min(5, len(short_ema_series) - 1)
            if lookback_count < 2:
                return 0.0

            differences = []
            for offset in range(lookback_count):
                position = -(offset + 1)
                short_value = short_ema_series.iloc[position]
                long_value = long_ema_series.iloc[position]

                if pd.isna(short_value) or pd.isna(long_value):
                    continue

                differences.append(short_value - long_value)

            if len(differences) < 2:
                return 0.0

            differences.reverse()

            rate_of_change_values = []
            for change_index in range(1, len(differences)):
                change = abs(differences[change_index] - differences[change_index - 1])
                rate_of_change_values.append(change)

            if not rate_of_change_values:
                return 0.0

            average_rate_of_change = sum(rate_of_change_values) / len(rate_of_change_values)

            close_price_reference = abs(short_ema_series.iloc[-1])
            if close_price_reference == 0:
                return 0.0

            normalized_speed = min(average_rate_of_change / close_price_reference * 1000, 1.0)

            return round(normalized_speed, 4)

        except Exception as speed_error:
            self.logger.debug(
                "Crossover speed calculation failed: %s", str(speed_error)
            )
            return 0.0
