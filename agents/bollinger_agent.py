"""
Gold Trading Analysis Platform - Bollinger Bands Analysis Agent.

This module implements the Bollinger Bands technical analysis agent that
detects price extremes and potential reversals by analyzing price position
relative to statistically derived upper and lower bands around a moving average.

Bollinger Bands consist of a middle band (SMA), an upper band (SMA + N standard
deviations), and a lower band (SMA - N standard deviations). Price touching or
breaking the lower band suggests oversold conditions (CALL), while touching or
breaking the upper band suggests overbought conditions (PUT).
"""

from typing import Optional

import pandas as pd
import ta

from agents.base_agent import BaseAnalysisAgent, TradeDirection, TradeSignal
from config import PLATFORM_CONFIG


class BollingerBandsAgent(BaseAnalysisAgent):
    """Bollinger Bands technical analysis agent for detecting price channel extremes.

    This agent calculates Bollinger Bands using the configured period and
    standard deviation parameters, then generates trading signals when price
    approaches or breaches the bands. It also monitors bandwidth for squeeze
    conditions that may precede breakouts.

    Configuration values are sourced from PLATFORM_CONFIG.agent:
        - BOLLINGER_PERIOD: Moving average period for band calculation (default: 20).
        - BOLLINGER_STANDARD_DEVIATION: Number of standard deviations (default: 2.0).
        - MINIMUM_CANDLES_FOR_ANALYSIS: Minimum data points required (default: 30).
        - MINIMUM_CONFIDENCE_THRESHOLD: Minimum confidence for a signal (default: 0.55).

    Attributes:
        bollinger_period: The moving average period for band calculation.
        bollinger_standard_deviation: Number of standard deviations for band width.
        minimum_candles_for_analysis: Minimum candle count needed for valid analysis.
        minimum_confidence_threshold: Minimum confidence required for a directional signal.
    """

    def __init__(self) -> None:
        """Initialize the Bollinger Bands analysis agent.

        Loads all Bollinger-specific configuration parameters from PLATFORM_CONFIG.agent
        and initializes the base agent with identification details.
        """
        super().__init__(
            agent_name="BollingerBandsAgent",
            agent_description=(
                "Analyzes Bollinger Bands to detect price extremes and potential "
                "mean-reversion opportunities, generating CALL signals when price "
                "touches the lower band and PUT signals when price touches the "
                "upper band, with bandwidth squeeze detection for breakout alerts."
            ),
        )
        self.bollinger_period: int = PLATFORM_CONFIG.agent.BOLLINGER_PERIOD
        self.bollinger_standard_deviation: float = PLATFORM_CONFIG.agent.BOLLINGER_STANDARD_DEVIATION
        self.minimum_candles_for_analysis: int = PLATFORM_CONFIG.agent.MINIMUM_CANDLES_FOR_ANALYSIS
        self.minimum_confidence_threshold: float = PLATFORM_CONFIG.agent.MINIMUM_CONFIDENCE_THRESHOLD

    def analyze(
        self,
        candles_dataframe: pd.DataFrame,
        historical_dataframe: Optional[pd.DataFrame] = None,
    ) -> TradeSignal:
        """Analyze price data using Bollinger Bands.

        Calculates upper, middle, and lower Bollinger Bands, then determines
        trade direction based on price position relative to the bands.
        Also checks bandwidth for squeeze conditions indicating low volatility
        that may precede significant price moves.

        Args:
            candles_dataframe: DataFrame containing OHLCV candle data with
                at least a 'close' column.
            historical_dataframe: Optional DataFrame containing additional
                historical data for extended analysis context.

        Returns:
            A TradeSignal with:
                - CALL direction if price touches/breaks lower band.
                - PUT direction if price touches/breaks upper band.
                - NEUTRAL direction if price is within the bands.
                - Confidence based on distance from band and bandwidth.
                - indicator_values containing upper_band, middle_band,
                  lower_band, and bandwidth.
        """
        if not self._has_sufficient_data(candles_dataframe, self.minimum_candles_for_analysis):
            self.logger.warning(
                "Insufficient data for Bollinger Bands analysis. Required: %d, Available: %d",
                self.minimum_candles_for_analysis,
                len(candles_dataframe) if candles_dataframe is not None else 0,
            )
            return self._create_signal(
                direction=TradeDirection.NEUTRAL,
                confidence=0.0,
                reasoning="Insufficient data for Bollinger Bands analysis.",
                indicator_values={
                    "upper_band": None,
                    "middle_band": None,
                    "lower_band": None,
                    "bandwidth": None,
                },
            )

        try:
            bollinger_indicator = ta.volatility.BollingerBands(
                close=candles_dataframe["close"],
                window=self.bollinger_period,
                window_dev=self.bollinger_standard_deviation,
            )

            upper_band_series = bollinger_indicator.bollinger_hband()
            middle_band_series = bollinger_indicator.bollinger_mavg()
            lower_band_series = bollinger_indicator.bollinger_lband()
            bandwidth_series = bollinger_indicator.bollinger_wband()

            current_upper_band = upper_band_series.iloc[-1]
            current_middle_band = middle_band_series.iloc[-1]
            current_lower_band = lower_band_series.iloc[-1]
            current_bandwidth = bandwidth_series.iloc[-1]
            current_close_price = candles_dataframe["close"].iloc[-1]

            if any(
                pd.isna(value)
                for value in [current_upper_band, current_middle_band, current_lower_band, current_bandwidth]
            ):
                self.logger.warning("Bollinger Bands calculation returned NaN values.")
                return self._create_signal(
                    direction=TradeDirection.NEUTRAL,
                    confidence=0.0,
                    reasoning="Bollinger Bands calculation returned invalid values.",
                    indicator_values={
                        "upper_band": None,
                        "middle_band": None,
                        "lower_band": None,
                        "bandwidth": None,
                    },
                )

            indicator_values = {
                "upper_band": round(current_upper_band, 4),
                "middle_band": round(current_middle_band, 4),
                "lower_band": round(current_lower_band, 4),
                "bandwidth": round(current_bandwidth, 6),
            }

            band_range = current_upper_band - current_lower_band
            is_squeeze_active = self._detect_bandwidth_squeeze(bandwidth_series)

            if current_close_price <= current_lower_band:
                distance_below_band = current_lower_band - current_close_price
                normalized_distance = distance_below_band / band_range if band_range > 0 else 0.0
                raw_confidence = min(0.65 + normalized_distance * 2.0, 0.95)

                if is_squeeze_active:
                    raw_confidence = min(raw_confidence + 0.05, 1.0)

                reasoning = (
                    f"Price ({current_close_price:.4f}) at or below lower Bollinger Band "
                    f"({current_lower_band:.4f}). Band range: {band_range:.4f}. "
                    f"Bandwidth: {current_bandwidth:.6f}. "
                    f"{'Bandwidth squeeze detected, potential breakout imminent. ' if is_squeeze_active else ''}"
                    f"Price touching lower band suggests oversold condition and potential bounce."
                )

                return self._create_signal(
                    direction=TradeDirection.CALL,
                    confidence=raw_confidence,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

            elif current_close_price >= current_upper_band:
                distance_above_band = current_close_price - current_upper_band
                normalized_distance = distance_above_band / band_range if band_range > 0 else 0.0
                raw_confidence = min(0.65 + normalized_distance * 2.0, 0.95)

                if is_squeeze_active:
                    raw_confidence = min(raw_confidence + 0.05, 1.0)

                reasoning = (
                    f"Price ({current_close_price:.4f}) at or above upper Bollinger Band "
                    f"({current_upper_band:.4f}). Band range: {band_range:.4f}. "
                    f"Bandwidth: {current_bandwidth:.6f}. "
                    f"{'Bandwidth squeeze detected, potential breakout imminent. ' if is_squeeze_active else ''}"
                    f"Price touching upper band suggests overbought condition and potential reversal."
                )

                return self._create_signal(
                    direction=TradeDirection.PUT,
                    confidence=raw_confidence,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

            else:
                position_in_band = (current_close_price - current_lower_band) / band_range if band_range > 0 else 0.5

                near_lower_threshold = 0.15
                near_upper_threshold = 0.85

                if position_in_band < near_lower_threshold:
                    mild_confidence = 0.45 + (near_lower_threshold - position_in_band) * 2.0
                    reasoning = (
                        f"Price ({current_close_price:.4f}) is near lower Bollinger Band "
                        f"({current_lower_band:.4f}). Band position: {position_in_band:.2%}. "
                        f"Leaning toward potential bounce but not yet at band."
                    )
                    return self._create_signal(
                        direction=TradeDirection.CALL,
                        confidence=min(mild_confidence, 0.55),
                        reasoning=reasoning,
                        indicator_values=indicator_values,
                    )

                elif position_in_band > near_upper_threshold:
                    mild_confidence = 0.45 + (position_in_band - near_upper_threshold) * 2.0
                    reasoning = (
                        f"Price ({current_close_price:.4f}) is near upper Bollinger Band "
                        f"({current_upper_band:.4f}). Band position: {position_in_band:.2%}. "
                        f"Leaning toward potential reversal but not yet at band."
                    )
                    return self._create_signal(
                        direction=TradeDirection.PUT,
                        confidence=min(mild_confidence, 0.55),
                        reasoning=reasoning,
                        indicator_values=indicator_values,
                    )

                else:
                    reasoning = (
                        f"Price ({current_close_price:.4f}) is within Bollinger Bands. "
                        f"Upper: {current_upper_band:.4f}, Middle: {current_middle_band:.4f}, "
                        f"Lower: {current_lower_band:.4f}. Band position: {position_in_band:.2%}. "
                        f"No significant band interaction detected."
                    )

                    return self._create_signal(
                        direction=TradeDirection.NEUTRAL,
                        confidence=0.3,
                        reasoning=reasoning,
                        indicator_values=indicator_values,
                    )

        except Exception as analysis_error:
            self.logger.error(
                "Error during Bollinger Bands analysis: %s",
                str(analysis_error),
                exc_info=True,
            )
            return self._create_signal(
                direction=TradeDirection.NEUTRAL,
                confidence=0.0,
                reasoning=f"Bollinger Bands analysis failed due to error: {str(analysis_error)}",
                indicator_values={
                    "upper_band": None,
                    "middle_band": None,
                    "lower_band": None,
                    "bandwidth": None,
                },
            )

    def _detect_bandwidth_squeeze(self, bandwidth_series: pd.Series) -> bool:
        """Detect a Bollinger Band squeeze condition indicating low volatility.

        A squeeze occurs when the bandwidth narrows significantly compared to
        its recent history, suggesting that a large price move may be imminent.

        Args:
            bandwidth_series: Series containing Bollinger bandwidth values.

        Returns:
            True if a bandwidth squeeze is detected, False otherwise.
        """
        try:
            lookback_window = min(20, len(bandwidth_series))
            if lookback_window < 5:
                return False

            recent_bandwidth_values = bandwidth_series.iloc[-lookback_window:]

            if recent_bandwidth_values.isna().any():
                return False

            current_bandwidth = recent_bandwidth_values.iloc[-1]
            average_bandwidth = recent_bandwidth_values.mean()

            squeeze_threshold_ratio = 0.5
            is_squeeze = current_bandwidth < (average_bandwidth * squeeze_threshold_ratio)

            if is_squeeze:
                self.logger.info(
                    "Bollinger Band squeeze detected. Current bandwidth: %.6f, "
                    "Average bandwidth: %.6f",
                    current_bandwidth,
                    average_bandwidth,
                )

            return is_squeeze

        except Exception as squeeze_error:
            self.logger.debug(
                "Bandwidth squeeze detection failed: %s", str(squeeze_error)
            )
            return False
