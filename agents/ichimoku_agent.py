"""
Gold Trading Analysis Platform - Ichimoku Cloud Analysis Agent.

This module implements the Ichimoku Cloud (Ichimoku Kinko Hyo) technical analysis
agent that provides a comprehensive trend analysis framework for gold price data
using five calculated components.

The Ichimoku system consists of:
    - Conversion Line (Tenkan-sen): Short-term trend indicator.
    - Base Line (Kijun-sen): Medium-term trend indicator.
    - Span A (Senkou Span A): First cloud boundary (average of conversion and base).
    - Span B (Senkou Span B): Second cloud boundary (long-term equilibrium).
    - Lagging Span (Chikou Span): Current close plotted back in time.

Signals are generated based on price position relative to the cloud and the
relationship between conversion and base lines.
"""

from typing import Optional

import pandas as pd
import ta

from agents.base_agent import BaseAnalysisAgent, TradeDirection, TradeSignal
from config import PLATFORM_CONFIG


class IchimokuCloudAgent(BaseAnalysisAgent):
    """Ichimoku Cloud technical analysis agent for comprehensive trend analysis.

    This agent calculates all five Ichimoku components and generates trading
    signals based on price position relative to the cloud (Kumo) and the
    relationship between the conversion line and base line.

    Configuration values are sourced from PLATFORM_CONFIG.agent:
        - ICHIMOKU_CONVERSION_PERIOD: Tenkan-sen period (default: 9).
        - ICHIMOKU_BASE_PERIOD: Kijun-sen period (default: 26).
        - ICHIMOKU_SPAN_B_PERIOD: Senkou Span B period (default: 52).
        - ICHIMOKU_DISPLACEMENT: Cloud displacement period (default: 26).
        - MINIMUM_CANDLES_FOR_ANALYSIS: Minimum data points required (default: 30).
        - MINIMUM_CONFIDENCE_THRESHOLD: Minimum confidence for a signal (default: 0.55).

    Attributes:
        ichimoku_conversion_period: Conversion line (Tenkan-sen) period.
        ichimoku_base_period: Base line (Kijun-sen) period.
        ichimoku_span_b_period: Span B (Senkou Span B) period.
        ichimoku_displacement: Cloud displacement period.
        minimum_candles_for_analysis: Minimum candle count needed for valid analysis.
        minimum_confidence_threshold: Minimum confidence required for a directional signal.
    """

    def __init__(self) -> None:
        """Initialize the Ichimoku Cloud analysis agent.

        Loads all Ichimoku-specific configuration parameters from
        PLATFORM_CONFIG.agent and initializes the base agent with
        identification details.
        """
        super().__init__(
            agent_name="IchimokuCloudAgent",
            agent_description=(
                "Analyzes the Ichimoku Cloud (Ichimoku Kinko Hyo) system to provide "
                "comprehensive trend analysis, generating CALL signals when price is "
                "above the cloud with bullish line configuration, and PUT signals when "
                "price is below the cloud with bearish line configuration."
            ),
        )
        self.ichimoku_conversion_period: int = PLATFORM_CONFIG.agent.ICHIMOKU_CONVERSION_PERIOD
        self.ichimoku_base_period: int = PLATFORM_CONFIG.agent.ICHIMOKU_BASE_PERIOD
        self.ichimoku_span_b_period: int = PLATFORM_CONFIG.agent.ICHIMOKU_SPAN_B_PERIOD
        self.ichimoku_displacement: int = PLATFORM_CONFIG.agent.ICHIMOKU_DISPLACEMENT
        self.minimum_candles_for_analysis: int = PLATFORM_CONFIG.agent.MINIMUM_CANDLES_FOR_ANALYSIS
        self.minimum_confidence_threshold: float = PLATFORM_CONFIG.agent.MINIMUM_CONFIDENCE_THRESHOLD

    def analyze(
        self,
        candles_dataframe: pd.DataFrame,
        historical_dataframe: Optional[pd.DataFrame] = None,
    ) -> TradeSignal:
        """Analyze price data using the Ichimoku Cloud system.

        Calculates all Ichimoku components and determines trade direction
        based on price position relative to the cloud and the conversion
        line / base line relationship.

        Args:
            candles_dataframe: DataFrame containing OHLCV candle data with
                'high', 'low', and 'close' columns.
            historical_dataframe: Optional DataFrame containing additional
                historical data for extended analysis context.

        Returns:
            A TradeSignal with:
                - CALL direction when price is above cloud AND conversion > base.
                - PUT direction when price is below cloud AND conversion < base.
                - NEUTRAL direction when price is inside the cloud.
                - Confidence based on cloud distance and line convergence.
                - indicator_values containing conversion_line, base_line,
                  span_a, and span_b.
        """
        minimum_required_candles = max(
            self.minimum_candles_for_analysis,
            self.ichimoku_span_b_period + self.ichimoku_displacement,
        )

        if not self._has_sufficient_data(candles_dataframe, minimum_required_candles):
            self.logger.warning(
                "Insufficient data for Ichimoku analysis. Required: %d, Available: %d",
                minimum_required_candles,
                len(candles_dataframe) if candles_dataframe is not None else 0,
            )
            return self._create_signal(
                direction=TradeDirection.NEUTRAL,
                confidence=0.0,
                reasoning="Insufficient data for Ichimoku Cloud analysis.",
                indicator_values={
                    "conversion_line": None,
                    "base_line": None,
                    "span_a": None,
                    "span_b": None,
                },
            )

        try:
            ichimoku_indicator = ta.trend.IchimokuIndicator(
                high=candles_dataframe["high"],
                low=candles_dataframe["low"],
                window1=self.ichimoku_conversion_period,
                window2=self.ichimoku_base_period,
                window3=self.ichimoku_span_b_period,
            )

            conversion_line_series = ichimoku_indicator.ichimoku_conversion_line()
            base_line_series = ichimoku_indicator.ichimoku_base_line()
            span_a_series = ichimoku_indicator.ichimoku_a()
            span_b_series = ichimoku_indicator.ichimoku_b()

            current_conversion_line = conversion_line_series.iloc[-1]
            current_base_line = base_line_series.iloc[-1]
            current_span_a = span_a_series.iloc[-1]
            current_span_b = span_b_series.iloc[-1]
            current_close_price = candles_dataframe["close"].iloc[-1]

            if any(
                pd.isna(value)
                for value in [current_conversion_line, current_base_line, current_span_a, current_span_b]
            ):
                self.logger.warning("Ichimoku calculation returned NaN values.")
                return self._create_signal(
                    direction=TradeDirection.NEUTRAL,
                    confidence=0.0,
                    reasoning="Ichimoku calculation returned invalid values.",
                    indicator_values={
                        "conversion_line": None,
                        "base_line": None,
                        "span_a": None,
                        "span_b": None,
                    },
                )

            indicator_values = {
                "conversion_line": round(current_conversion_line, 4),
                "base_line": round(current_base_line, 4),
                "span_a": round(current_span_a, 4),
                "span_b": round(current_span_b, 4),
            }

            cloud_upper_boundary = max(current_span_a, current_span_b)
            cloud_lower_boundary = min(current_span_a, current_span_b)
            cloud_thickness = cloud_upper_boundary - cloud_lower_boundary

            is_price_above_cloud = current_close_price > cloud_upper_boundary
            is_price_below_cloud = current_close_price < cloud_lower_boundary
            is_price_inside_cloud = not is_price_above_cloud and not is_price_below_cloud

            is_conversion_above_base = current_conversion_line > current_base_line
            is_conversion_below_base = current_conversion_line < current_base_line

            if is_price_above_cloud and is_conversion_above_base:
                cloud_distance = current_close_price - cloud_upper_boundary
                cloud_distance_factor = min(cloud_distance / cloud_upper_boundary * 100, 0.25) if cloud_upper_boundary > 0 else 0.0

                line_convergence = abs(current_conversion_line - current_base_line)
                line_convergence_factor = min(line_convergence / current_base_line * 100, 0.2) if current_base_line > 0 else 0.0

                raw_confidence = min(0.6 + cloud_distance_factor + line_convergence_factor, 0.95)

                reasoning = (
                    f"Price ({current_close_price:.4f}) is ABOVE the Ichimoku Cloud "
                    f"(upper boundary: {cloud_upper_boundary:.4f}). "
                    f"Conversion line ({current_conversion_line:.4f}) > Base line ({current_base_line:.4f}). "
                    f"Cloud thickness: {cloud_thickness:.4f}. "
                    f"Distance above cloud: {cloud_distance:.4f}. "
                    f"Strong bullish configuration with price above cloud and bullish line alignment."
                )

                return self._create_signal(
                    direction=TradeDirection.CALL,
                    confidence=raw_confidence,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

            elif is_price_below_cloud and is_conversion_below_base:
                cloud_distance = cloud_lower_boundary - current_close_price
                cloud_distance_factor = min(cloud_distance / cloud_lower_boundary * 100, 0.25) if cloud_lower_boundary > 0 else 0.0

                line_convergence = abs(current_base_line - current_conversion_line)
                line_convergence_factor = min(line_convergence / current_base_line * 100, 0.2) if current_base_line > 0 else 0.0

                raw_confidence = min(0.6 + cloud_distance_factor + line_convergence_factor, 0.95)

                reasoning = (
                    f"Price ({current_close_price:.4f}) is BELOW the Ichimoku Cloud "
                    f"(lower boundary: {cloud_lower_boundary:.4f}). "
                    f"Conversion line ({current_conversion_line:.4f}) < Base line ({current_base_line:.4f}). "
                    f"Cloud thickness: {cloud_thickness:.4f}. "
                    f"Distance below cloud: {cloud_distance:.4f}. "
                    f"Strong bearish configuration with price below cloud and bearish line alignment."
                )

                return self._create_signal(
                    direction=TradeDirection.PUT,
                    confidence=raw_confidence,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

            elif is_price_above_cloud and is_conversion_below_base:
                reasoning = (
                    f"Price ({current_close_price:.4f}) is above cloud but conversion line "
                    f"({current_conversion_line:.4f}) < base line ({current_base_line:.4f}). "
                    f"Mixed signal: price is bullish but line configuration is bearish. "
                    f"Potential weakening of bullish trend."
                )

                return self._create_signal(
                    direction=TradeDirection.CALL,
                    confidence=0.45,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

            elif is_price_below_cloud and is_conversion_above_base:
                reasoning = (
                    f"Price ({current_close_price:.4f}) is below cloud but conversion line "
                    f"({current_conversion_line:.4f}) > base line ({current_base_line:.4f}). "
                    f"Mixed signal: price is bearish but line configuration is bullish. "
                    f"Potential weakening of bearish trend."
                )

                return self._create_signal(
                    direction=TradeDirection.PUT,
                    confidence=0.45,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

            elif is_price_inside_cloud:
                cloud_midpoint = (cloud_upper_boundary + cloud_lower_boundary) / 2.0
                position_in_cloud = "upper half" if current_close_price > cloud_midpoint else "lower half"

                reasoning = (
                    f"Price ({current_close_price:.4f}) is INSIDE the Ichimoku Cloud "
                    f"(upper: {cloud_upper_boundary:.4f}, lower: {cloud_lower_boundary:.4f}). "
                    f"Price is in the {position_in_cloud} of the cloud. "
                    f"Cloud thickness: {cloud_thickness:.4f}. "
                    f"Conversion line: {current_conversion_line:.4f}, "
                    f"Base line: {current_base_line:.4f}. "
                    f"Price inside cloud indicates indecision and potential trend transition."
                )

                return self._create_signal(
                    direction=TradeDirection.NEUTRAL,
                    confidence=0.3,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

            else:
                reasoning = (
                    f"Ichimoku analysis inconclusive. "
                    f"Price: {current_close_price:.4f}, "
                    f"Conversion: {current_conversion_line:.4f}, "
                    f"Base: {current_base_line:.4f}, "
                    f"Span A: {current_span_a:.4f}, Span B: {current_span_b:.4f}."
                )

                return self._create_signal(
                    direction=TradeDirection.NEUTRAL,
                    confidence=0.25,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

        except Exception as analysis_error:
            self.logger.error(
                "Error during Ichimoku Cloud analysis: %s",
                str(analysis_error),
                exc_info=True,
            )
            return self._create_signal(
                direction=TradeDirection.NEUTRAL,
                confidence=0.0,
                reasoning=f"Ichimoku Cloud analysis failed due to error: {str(analysis_error)}",
                indicator_values={
                    "conversion_line": None,
                    "base_line": None,
                    "span_a": None,
                    "span_b": None,
                },
            )
