"""
Gold Trading Analysis Platform - Stochastic Oscillator Analysis Agent.

This module implements the Stochastic Oscillator technical analysis agent
that detects momentum shifts and overbought/oversold conditions in gold
price data using the %K and %D stochastic lines.

The Stochastic Oscillator compares a closing price to its price range over
a given period. %K is the raw stochastic value and %D is a smoothed version.
Trading signals are generated when %K crosses %D in extreme zones (overbought
above 80, oversold below 20).
"""

from typing import Optional

import pandas as pd
import ta

from agents.base_agent import BaseAnalysisAgent, TradeDirection, TradeSignal
from config import PLATFORM_CONFIG


class StochasticOscillatorAgent(BaseAnalysisAgent):
    """Stochastic Oscillator technical analysis agent for momentum detection.

    This agent calculates the Stochastic Oscillator using configured %K and %D
    periods, then generates trading signals based on %K-%D crossovers within
    overbought and oversold zones. Signal confidence is derived from the depth
    within the extreme zone and the clarity of the crossover.

    Configuration values are sourced from PLATFORM_CONFIG.agent:
        - STOCHASTIC_K_PERIOD: %K calculation period (default: 14).
        - STOCHASTIC_D_PERIOD: %D smoothing period (default: 3).
        - STOCHASTIC_OVERBOUGHT_THRESHOLD: Overbought level (default: 80.0).
        - STOCHASTIC_OVERSOLD_THRESHOLD: Oversold level (default: 20.0).
        - MINIMUM_CANDLES_FOR_ANALYSIS: Minimum data points required (default: 30).
        - MINIMUM_CONFIDENCE_THRESHOLD: Minimum confidence for a signal (default: 0.55).

    Attributes:
        stochastic_k_period: %K calculation period.
        stochastic_d_period: %D smoothing period.
        stochastic_overbought_threshold: Level above which market is overbought.
        stochastic_oversold_threshold: Level below which market is oversold.
        minimum_candles_for_analysis: Minimum candle count needed for valid analysis.
        minimum_confidence_threshold: Minimum confidence required for a directional signal.
    """

    def __init__(self) -> None:
        """Initialize the Stochastic Oscillator analysis agent.

        Loads all stochastic-specific configuration parameters from
        PLATFORM_CONFIG.agent and initializes the base agent with
        identification details.
        """
        super().__init__(
            agent_name="StochasticOscillatorAgent",
            agent_description=(
                "Analyzes the Stochastic Oscillator to detect momentum shifts "
                "through %K-%D crossovers in overbought and oversold zones, "
                "generating CALL signals on bullish crossovers in oversold "
                "territory and PUT signals on bearish crossovers in overbought "
                "territory."
            ),
        )
        self.stochastic_k_period: int = PLATFORM_CONFIG.agent.STOCHASTIC_K_PERIOD
        self.stochastic_d_period: int = PLATFORM_CONFIG.agent.STOCHASTIC_D_PERIOD
        self.stochastic_overbought_threshold: float = PLATFORM_CONFIG.agent.STOCHASTIC_OVERBOUGHT_THRESHOLD
        self.stochastic_oversold_threshold: float = PLATFORM_CONFIG.agent.STOCHASTIC_OVERSOLD_THRESHOLD
        self.minimum_candles_for_analysis: int = PLATFORM_CONFIG.agent.MINIMUM_CANDLES_FOR_ANALYSIS
        self.minimum_confidence_threshold: float = PLATFORM_CONFIG.agent.MINIMUM_CONFIDENCE_THRESHOLD

    def analyze(
        self,
        candles_dataframe: pd.DataFrame,
        historical_dataframe: Optional[pd.DataFrame] = None,
    ) -> TradeSignal:
        """Analyze price data using the Stochastic Oscillator.

        Calculates %K and %D stochastic values, then detects crossover
        events within overbought and oversold zones to determine trade
        direction and confidence.

        Args:
            candles_dataframe: DataFrame containing OHLCV candle data with
                'high', 'low', and 'close' columns.
            historical_dataframe: Optional DataFrame containing additional
                historical data for extended analysis context.

        Returns:
            A TradeSignal with:
                - CALL direction on bullish %K-%D crossover in oversold zone.
                - PUT direction on bearish %K-%D crossover in overbought zone.
                - NEUTRAL direction if no actionable crossover detected.
                - Confidence based on zone depth and crossover clarity.
                - indicator_values containing k_value and d_value.
        """
        if not self._has_sufficient_data(candles_dataframe, self.minimum_candles_for_analysis):
            self.logger.warning(
                "Insufficient data for Stochastic Oscillator analysis. Required: %d, Available: %d",
                self.minimum_candles_for_analysis,
                len(candles_dataframe) if candles_dataframe is not None else 0,
            )
            return self._create_signal(
                direction=TradeDirection.NEUTRAL,
                confidence=0.0,
                reasoning="Insufficient data for Stochastic Oscillator analysis.",
                indicator_values={"k_value": None, "d_value": None},
            )

        try:
            stochastic_indicator = ta.momentum.StochasticOscillator(
                high=candles_dataframe["high"],
                low=candles_dataframe["low"],
                close=candles_dataframe["close"],
                window=self.stochastic_k_period,
                smooth_window=self.stochastic_d_period,
            )

            k_series = stochastic_indicator.stoch()
            d_series = stochastic_indicator.stoch_signal()

            current_k_value = k_series.iloc[-1]
            current_d_value = d_series.iloc[-1]

            if pd.isna(current_k_value) or pd.isna(current_d_value):
                self.logger.warning("Stochastic calculation returned NaN values.")
                return self._create_signal(
                    direction=TradeDirection.NEUTRAL,
                    confidence=0.0,
                    reasoning="Stochastic Oscillator calculation returned invalid values.",
                    indicator_values={"k_value": None, "d_value": None},
                )

            indicator_values = {
                "k_value": round(current_k_value, 4),
                "d_value": round(current_d_value, 4),
            }

            crossover_type = self._detect_stochastic_crossover(
                k_series=k_series,
                d_series=d_series,
            )

            is_in_oversold_zone = current_k_value < self.stochastic_oversold_threshold
            is_in_overbought_zone = current_k_value > self.stochastic_overbought_threshold

            if crossover_type == "bullish" and is_in_oversold_zone:
                zone_depth = self.stochastic_oversold_threshold - current_k_value
                maximum_zone_depth = self.stochastic_oversold_threshold
                zone_depth_factor = zone_depth / maximum_zone_depth if maximum_zone_depth > 0 else 0.0

                crossover_clarity = abs(current_k_value - current_d_value)
                clarity_factor = min(crossover_clarity / 10.0, 0.3)

                raw_confidence = min(0.6 + zone_depth_factor * 0.25 + clarity_factor, 0.95)

                reasoning = (
                    f"Stochastic %%K ({current_k_value:.2f}) crossed above %%D ({current_d_value:.2f}) "
                    f"in oversold zone (below {self.stochastic_oversold_threshold:.1f}). "
                    f"Zone depth: {zone_depth:.2f}. Crossover clarity: {crossover_clarity:.2f}. "
                    f"Bullish momentum shift detected in oversold territory."
                )

                return self._create_signal(
                    direction=TradeDirection.CALL,
                    confidence=raw_confidence,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

            elif crossover_type == "bearish" and is_in_overbought_zone:
                zone_depth = current_k_value - self.stochastic_overbought_threshold
                maximum_zone_depth = 100.0 - self.stochastic_overbought_threshold
                zone_depth_factor = zone_depth / maximum_zone_depth if maximum_zone_depth > 0 else 0.0

                crossover_clarity = abs(current_k_value - current_d_value)
                clarity_factor = min(crossover_clarity / 10.0, 0.3)

                raw_confidence = min(0.6 + zone_depth_factor * 0.25 + clarity_factor, 0.95)

                reasoning = (
                    f"Stochastic %%K ({current_k_value:.2f}) crossed below %%D ({current_d_value:.2f}) "
                    f"in overbought zone (above {self.stochastic_overbought_threshold:.1f}). "
                    f"Zone depth: {zone_depth:.2f}. Crossover clarity: {crossover_clarity:.2f}. "
                    f"Bearish momentum shift detected in overbought territory."
                )

                return self._create_signal(
                    direction=TradeDirection.PUT,
                    confidence=raw_confidence,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

            elif crossover_type == "bullish" and not is_in_oversold_zone:
                reasoning = (
                    f"Stochastic %%K ({current_k_value:.2f}) crossed above %%D ({current_d_value:.2f}) "
                    f"but NOT in oversold zone. Crossover outside extreme zone has lower reliability."
                )
                return self._create_signal(
                    direction=TradeDirection.CALL,
                    confidence=0.45,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

            elif crossover_type == "bearish" and not is_in_overbought_zone:
                reasoning = (
                    f"Stochastic %%K ({current_k_value:.2f}) crossed below %%D ({current_d_value:.2f}) "
                    f"but NOT in overbought zone. Crossover outside extreme zone has lower reliability."
                )
                return self._create_signal(
                    direction=TradeDirection.PUT,
                    confidence=0.45,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

            else:
                zone_description = "neutral zone"
                if is_in_oversold_zone:
                    zone_description = "oversold zone"
                elif is_in_overbought_zone:
                    zone_description = "overbought zone"

                reasoning = (
                    f"No actionable Stochastic crossover detected. "
                    f"%%K: {current_k_value:.2f}, %%D: {current_d_value:.2f}. "
                    f"Currently in {zone_description}. "
                    f"Waiting for %K-%D crossover in an extreme zone."
                )

                return self._create_signal(
                    direction=TradeDirection.NEUTRAL,
                    confidence=0.3,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

        except Exception as analysis_error:
            self.logger.error(
                "Error during Stochastic Oscillator analysis: %s",
                str(analysis_error),
                exc_info=True,
            )
            return self._create_signal(
                direction=TradeDirection.NEUTRAL,
                confidence=0.0,
                reasoning=f"Stochastic Oscillator analysis failed due to error: {str(analysis_error)}",
                indicator_values={"k_value": None, "d_value": None},
            )

    def _detect_stochastic_crossover(
        self,
        k_series: pd.Series,
        d_series: pd.Series,
    ) -> Optional[str]:
        """Detect %K-%D crossover events in recent stochastic data.

        Examines the most recent data points to determine if %K has crossed
        above or below %D, indicating a momentum shift.

        Args:
            k_series: Series containing %K stochastic values.
            d_series: Series containing %D stochastic values.

        Returns:
            "bullish" if %K crossed above %D,
            "bearish" if %K crossed below %D,
            None if no crossover was detected.
        """
        try:
            lookback_window = min(3, len(k_series) - 1)
            if lookback_window < 1:
                return None

            for period_index in range(1, lookback_window + 1):
                current_position = -1
                previous_position = -(period_index + 1)

                if abs(previous_position) > len(k_series):
                    continue

                current_k = k_series.iloc[current_position]
                previous_k = k_series.iloc[previous_position]
                current_d = d_series.iloc[current_position]
                previous_d = d_series.iloc[previous_position]

                if any(pd.isna(value) for value in [current_k, previous_k, current_d, previous_d]):
                    continue

                if previous_k <= previous_d and current_k > current_d:
                    return "bullish"

                if previous_k >= previous_d and current_k < current_d:
                    return "bearish"

            return None

        except Exception as crossover_error:
            self.logger.debug(
                "Stochastic crossover detection failed: %s", str(crossover_error)
            )
            return None
