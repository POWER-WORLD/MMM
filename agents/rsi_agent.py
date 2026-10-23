"""
Gold Trading Analysis Platform - RSI (Relative Strength Index) Analysis Agent.

This module implements the Relative Strength Index technical analysis agent
that detects overbought and oversold conditions in gold price data to
generate trading signals.

The RSI oscillates between 0 and 100, with readings below 30 indicating
oversold conditions (potential CALL signal) and readings above 70 indicating
overbought conditions (potential PUT signal). Divergence between RSI and
price action is also analyzed for stronger signal confirmation.
"""

from typing import Optional

import pandas as pd
import ta

from agents.base_agent import BaseAnalysisAgent, TradeDirection, TradeSignal
from config import PLATFORM_CONFIG


class RelativeStrengthIndexAgent(BaseAnalysisAgent):
    """RSI-based technical analysis agent for detecting overbought/oversold conditions.

    This agent calculates the Relative Strength Index using the configured period
    and threshold values, then generates trading signals when the RSI enters
    extreme zones. It also checks for RSI-price divergence to strengthen signals.

    Configuration values are sourced from PLATFORM_CONFIG.agent:
        - RSI_PERIOD: Lookback period for RSI calculation (default: 14).
        - RSI_OVERBOUGHT_THRESHOLD: Level above which market is overbought (default: 70.0).
        - RSI_OVERSOLD_THRESHOLD: Level below which market is oversold (default: 30.0).
        - MINIMUM_CANDLES_FOR_ANALYSIS: Minimum data points required (default: 30).
        - MINIMUM_CONFIDENCE_THRESHOLD: Minimum confidence to issue a signal (default: 0.55).

    Attributes:
        rsi_period: The lookback period for RSI calculation.
        rsi_overbought_threshold: The RSI level indicating overbought conditions.
        rsi_oversold_threshold: The RSI level indicating oversold conditions.
        minimum_candles_for_analysis: Minimum candle count needed for valid analysis.
        minimum_confidence_threshold: Minimum confidence required for a directional signal.
    """

    def __init__(self) -> None:
        """Initialize the Relative Strength Index analysis agent.

        Loads all RSI-specific configuration parameters from PLATFORM_CONFIG.agent
        and initializes the base agent with identification details.
        """
        super().__init__(
            agent_name="RelativeStrengthIndexAgent",
            agent_description=(
                "Analyzes the Relative Strength Index (RSI) to detect overbought "
                "and oversold conditions, generating CALL signals in oversold zones "
                "and PUT signals in overbought zones with divergence confirmation."
            ),
        )
        self.rsi_period: int = PLATFORM_CONFIG.agent.RSI_PERIOD
        self.rsi_overbought_threshold: float = PLATFORM_CONFIG.agent.RSI_OVERBOUGHT_THRESHOLD
        self.rsi_oversold_threshold: float = PLATFORM_CONFIG.agent.RSI_OVERSOLD_THRESHOLD
        self.minimum_candles_for_analysis: int = PLATFORM_CONFIG.agent.MINIMUM_CANDLES_FOR_ANALYSIS
        self.minimum_confidence_threshold: float = PLATFORM_CONFIG.agent.MINIMUM_CONFIDENCE_THRESHOLD

    def analyze(
        self,
        candles_dataframe: pd.DataFrame,
        historical_dataframe: Optional[pd.DataFrame] = None,
    ) -> TradeSignal:
        """Analyze price data using the Relative Strength Index indicator.

        Calculates the RSI from closing prices and determines trade direction
        based on overbought/oversold thresholds. Also checks for RSI-price
        divergence to provide additional signal strength.

        Args:
            candles_dataframe: DataFrame containing OHLCV candle data with
                at least a 'close' column.
            historical_dataframe: Optional DataFrame containing additional
                historical data for extended divergence analysis.

        Returns:
            A TradeSignal with:
                - CALL direction if RSI is in oversold territory (below threshold).
                - PUT direction if RSI is in overbought territory (above threshold).
                - NEUTRAL direction if RSI is between thresholds.
                - Confidence scaled by distance from threshold and divergence.
                - indicator_values containing the current RSI reading.
        """
        if not self._has_sufficient_data(candles_dataframe, self.minimum_candles_for_analysis):
            self.logger.warning(
                "Insufficient data for RSI analysis. Required: %d, Available: %d",
                self.minimum_candles_for_analysis,
                len(candles_dataframe) if candles_dataframe is not None else 0,
            )
            return self._create_signal(
                direction=TradeDirection.NEUTRAL,
                confidence=0.0,
                reasoning="Insufficient data for RSI analysis.",
                indicator_values={"rsi_value": None},
            )

        try:
            rsi_indicator = ta.momentum.RSIIndicator(
                close=candles_dataframe["close"],
                window=self.rsi_period,
            )
            rsi_series = rsi_indicator.rsi()
            current_rsi_value = rsi_series.iloc[-1]

            if pd.isna(current_rsi_value):
                self.logger.warning("RSI calculation returned NaN value.")
                return self._create_signal(
                    direction=TradeDirection.NEUTRAL,
                    confidence=0.0,
                    reasoning="RSI calculation returned invalid value.",
                    indicator_values={"rsi_value": None},
                )

            indicator_values = {"rsi_value": round(current_rsi_value, 4)}

            divergence_detected = self._check_rsi_divergence(
                candles_dataframe=candles_dataframe,
                rsi_series=rsi_series,
            )

            if current_rsi_value < self.rsi_oversold_threshold:
                distance_from_threshold = self.rsi_oversold_threshold - current_rsi_value
                maximum_possible_distance = self.rsi_oversold_threshold
                raw_confidence = distance_from_threshold / maximum_possible_distance

                if divergence_detected == "bullish":
                    raw_confidence = min(raw_confidence + 0.15, 1.0)

                confidence = min(raw_confidence, 1.0)

                reasoning = (
                    f"RSI at {current_rsi_value:.2f} is below oversold threshold "
                    f"of {self.rsi_oversold_threshold:.1f}. "
                    f"Distance from threshold: {distance_from_threshold:.2f}. "
                    f"{'Bullish divergence detected, strengthening signal.' if divergence_detected == 'bullish' else 'No divergence detected.'}"
                )

                return self._create_signal(
                    direction=TradeDirection.CALL,
                    confidence=confidence,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

            elif current_rsi_value > self.rsi_overbought_threshold:
                distance_from_threshold = current_rsi_value - self.rsi_overbought_threshold
                maximum_possible_distance = 100.0 - self.rsi_overbought_threshold
                raw_confidence = distance_from_threshold / maximum_possible_distance

                if divergence_detected == "bearish":
                    raw_confidence = min(raw_confidence + 0.15, 1.0)

                confidence = min(raw_confidence, 1.0)

                reasoning = (
                    f"RSI at {current_rsi_value:.2f} is above overbought threshold "
                    f"of {self.rsi_overbought_threshold:.1f}. "
                    f"Distance from threshold: {distance_from_threshold:.2f}. "
                    f"{'Bearish divergence detected, strengthening signal.' if divergence_detected == 'bearish' else 'No divergence detected.'}"
                )

                return self._create_signal(
                    direction=TradeDirection.PUT,
                    confidence=confidence,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

            else:
                reasoning = (
                    f"RSI at {current_rsi_value:.2f} is between oversold "
                    f"({self.rsi_oversold_threshold:.1f}) and overbought "
                    f"({self.rsi_overbought_threshold:.1f}) thresholds. "
                    f"No clear overbought/oversold condition detected."
                )

                return self._create_signal(
                    direction=TradeDirection.NEUTRAL,
                    confidence=0.3,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

        except Exception as analysis_error:
            self.logger.error(
                "Error during RSI analysis: %s", str(analysis_error), exc_info=True
            )
            return self._create_signal(
                direction=TradeDirection.NEUTRAL,
                confidence=0.0,
                reasoning=f"RSI analysis failed due to error: {str(analysis_error)}",
                indicator_values={"rsi_value": None},
            )

    def _check_rsi_divergence(
        self,
        candles_dataframe: pd.DataFrame,
        rsi_series: pd.Series,
    ) -> Optional[str]:
        """Check for divergence between RSI and price action.

        Bullish divergence occurs when price makes lower lows but RSI makes
        higher lows, suggesting potential upward reversal. Bearish divergence
        occurs when price makes higher highs but RSI makes lower highs,
        suggesting potential downward reversal.

        Args:
            candles_dataframe: DataFrame containing OHLCV candle data.
            rsi_series: Series containing calculated RSI values.

        Returns:
            "bullish" if bullish divergence is detected,
            "bearish" if bearish divergence is detected,
            None if no divergence is detected.
        """
        try:
            lookback_period = min(10, len(candles_dataframe) - 1)
            if lookback_period < 5:
                return None

            recent_close_prices = candles_dataframe["close"].iloc[-lookback_period:]
            recent_rsi_values = rsi_series.iloc[-lookback_period:]

            if recent_rsi_values.isna().any():
                return None

            price_midpoint = lookback_period // 2
            first_half_price_low = recent_close_prices.iloc[:price_midpoint].min()
            second_half_price_low = recent_close_prices.iloc[price_midpoint:].min()
            first_half_rsi_low = recent_rsi_values.iloc[:price_midpoint].min()
            second_half_rsi_low = recent_rsi_values.iloc[price_midpoint:].min()

            if (
                second_half_price_low < first_half_price_low
                and second_half_rsi_low > first_half_rsi_low
            ):
                self.logger.info("Bullish RSI divergence detected.")
                return "bullish"

            first_half_price_high = recent_close_prices.iloc[:price_midpoint].max()
            second_half_price_high = recent_close_prices.iloc[price_midpoint:].max()
            first_half_rsi_high = recent_rsi_values.iloc[:price_midpoint].max()
            second_half_rsi_high = recent_rsi_values.iloc[price_midpoint:].max()

            if (
                second_half_price_high > first_half_price_high
                and second_half_rsi_high < first_half_rsi_high
            ):
                self.logger.info("Bearish RSI divergence detected.")
                return "bearish"

            return None

        except Exception as divergence_error:
            self.logger.debug(
                "Divergence check failed: %s", str(divergence_error)
            )
            return None
