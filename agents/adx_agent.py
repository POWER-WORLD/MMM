"""
Gold Trading Analysis Platform - ADX (Average Directional Index) Analysis Agent.

This module implements the Average Directional Index technical analysis agent
that measures trend strength and direction in gold price data using the ADX
indicator along with the positive and negative directional indicators (DI+ and DI-).

The ADX measures trend strength on a scale of 0-100, with values above 25
indicating a strong trend. The DI+ and DI- components determine trend direction:
DI+ above DI- indicates bullish momentum, while DI- above DI+ indicates bearish
momentum.
"""

from typing import Optional

import pandas as pd
import ta

from agents.base_agent import BaseAnalysisAgent, TradeDirection, TradeSignal
from config import PLATFORM_CONFIG


class AverageDirectionalIndexAgent(BaseAnalysisAgent):
    """ADX-based technical analysis agent for measuring trend strength and direction.

    This agent calculates the Average Directional Index along with positive
    and negative directional indicators, then generates trading signals when
    a strong trend is detected (ADX above threshold) based on the DI+/DI-
    relationship.

    Configuration values are sourced from PLATFORM_CONFIG.agent:
        - ADX_PERIOD: ADX calculation period (default: 14).
        - ADX_TREND_STRENGTH_THRESHOLD: Minimum ADX for strong trend (default: 25.0).
        - MINIMUM_CANDLES_FOR_ANALYSIS: Minimum data points required (default: 30).
        - MINIMUM_CONFIDENCE_THRESHOLD: Minimum confidence for a signal (default: 0.55).

    Attributes:
        adx_period: The ADX calculation period.
        adx_trend_strength_threshold: Minimum ADX value indicating a strong trend.
        minimum_candles_for_analysis: Minimum candle count needed for valid analysis.
        minimum_confidence_threshold: Minimum confidence required for a directional signal.
    """

    def __init__(self) -> None:
        """Initialize the Average Directional Index analysis agent.

        Loads all ADX-specific configuration parameters from PLATFORM_CONFIG.agent
        and initializes the base agent with identification details.
        """
        super().__init__(
            agent_name="AverageDirectionalIndexAgent",
            agent_description=(
                "Analyzes the Average Directional Index (ADX) to measure trend "
                "strength and direction using DI+/DI- indicators, generating "
                "CALL signals when DI+ dominates in strong trends and PUT signals "
                "when DI- dominates in strong trends."
            ),
        )
        self.adx_period: int = PLATFORM_CONFIG.agent.ADX_PERIOD
        self.adx_trend_strength_threshold: float = PLATFORM_CONFIG.agent.ADX_TREND_STRENGTH_THRESHOLD
        self.minimum_candles_for_analysis: int = PLATFORM_CONFIG.agent.MINIMUM_CANDLES_FOR_ANALYSIS
        self.minimum_confidence_threshold: float = PLATFORM_CONFIG.agent.MINIMUM_CONFIDENCE_THRESHOLD

    def analyze(
        self,
        candles_dataframe: pd.DataFrame,
        historical_dataframe: Optional[pd.DataFrame] = None,
    ) -> TradeSignal:
        """Analyze price data using the Average Directional Index.

        Calculates ADX, DI+, and DI- values from price data, then determines
        trade direction based on trend strength (ADX level) and directional
        indicator dominance (DI+ vs DI-).

        Args:
            candles_dataframe: DataFrame containing OHLCV candle data with
                'high', 'low', and 'close' columns.
            historical_dataframe: Optional DataFrame containing additional
                historical data for extended analysis context.

        Returns:
            A TradeSignal with:
                - CALL direction when ADX > threshold and DI+ > DI-.
                - PUT direction when ADX > threshold and DI- > DI+.
                - NEUTRAL direction when ADX < threshold (weak trend).
                - Confidence based on ADX value and DI differential.
                - indicator_values containing adx_value, di_positive,
                  and di_negative.
        """
        if not self._has_sufficient_data(candles_dataframe, self.minimum_candles_for_analysis):
            self.logger.warning(
                "Insufficient data for ADX analysis. Required: %d, Available: %d",
                self.minimum_candles_for_analysis,
                len(candles_dataframe) if candles_dataframe is not None else 0,
            )
            return self._create_signal(
                direction=TradeDirection.NEUTRAL,
                confidence=0.0,
                reasoning="Insufficient data for ADX analysis.",
                indicator_values={
                    "adx_value": None,
                    "di_positive": None,
                    "di_negative": None,
                },
            )

        try:
            adx_indicator = ta.trend.ADXIndicator(
                high=candles_dataframe["high"],
                low=candles_dataframe["low"],
                close=candles_dataframe["close"],
                window=self.adx_period,
            )

            adx_series = adx_indicator.adx()
            di_positive_series = adx_indicator.adx_pos()
            di_negative_series = adx_indicator.adx_neg()

            current_adx_value = adx_series.iloc[-1]
            current_di_positive = di_positive_series.iloc[-1]
            current_di_negative = di_negative_series.iloc[-1]

            if pd.isna(current_adx_value) or pd.isna(current_di_positive) or pd.isna(current_di_negative):
                self.logger.warning("ADX calculation returned NaN values.")
                return self._create_signal(
                    direction=TradeDirection.NEUTRAL,
                    confidence=0.0,
                    reasoning="ADX calculation returned invalid values.",
                    indicator_values={
                        "adx_value": None,
                        "di_positive": None,
                        "di_negative": None,
                    },
                )

            indicator_values = {
                "adx_value": round(current_adx_value, 4),
                "di_positive": round(current_di_positive, 4),
                "di_negative": round(current_di_negative, 4),
            }

            is_strong_trend = current_adx_value >= self.adx_trend_strength_threshold

            if is_strong_trend:
                di_differential = current_di_positive - current_di_negative
                di_differential_absolute = abs(di_differential)

                adx_strength_factor = min((current_adx_value - self.adx_trend_strength_threshold) / 50.0, 0.3)
                di_differential_factor = min(di_differential_absolute / 40.0, 0.3)
                raw_confidence = min(0.55 + adx_strength_factor + di_differential_factor, 0.95)

                if current_di_positive > current_di_negative:
                    reasoning = (
                        f"ADX at {current_adx_value:.2f} indicates strong trend "
                        f"(above threshold of {self.adx_trend_strength_threshold:.1f}). "
                        f"DI+ ({current_di_positive:.2f}) > DI- ({current_di_negative:.2f}), "
                        f"differential: {di_differential:.2f}. "
                        f"Strong bullish trend with positive directional dominance."
                    )

                    return self._create_signal(
                        direction=TradeDirection.CALL,
                        confidence=raw_confidence,
                        reasoning=reasoning,
                        indicator_values=indicator_values,
                    )

                elif current_di_negative > current_di_positive:
                    reasoning = (
                        f"ADX at {current_adx_value:.2f} indicates strong trend "
                        f"(above threshold of {self.adx_trend_strength_threshold:.1f}). "
                        f"DI- ({current_di_negative:.2f}) > DI+ ({current_di_positive:.2f}), "
                        f"differential: {abs(di_differential):.2f}. "
                        f"Strong bearish trend with negative directional dominance."
                    )

                    return self._create_signal(
                        direction=TradeDirection.PUT,
                        confidence=raw_confidence,
                        reasoning=reasoning,
                        indicator_values=indicator_values,
                    )

                else:
                    reasoning = (
                        f"ADX at {current_adx_value:.2f} indicates strong trend, "
                        f"but DI+ ({current_di_positive:.2f}) equals DI- ({current_di_negative:.2f}). "
                        f"No clear directional bias despite trend strength."
                    )

                    return self._create_signal(
                        direction=TradeDirection.NEUTRAL,
                        confidence=0.35,
                        reasoning=reasoning,
                        indicator_values=indicator_values,
                    )

            else:
                reasoning = (
                    f"ADX at {current_adx_value:.2f} is below trend strength threshold "
                    f"of {self.adx_trend_strength_threshold:.1f}, indicating weak or "
                    f"ranging market. DI+ ({current_di_positive:.2f}), "
                    f"DI- ({current_di_negative:.2f}). "
                    f"No strong trend detected for directional trading."
                )

                return self._create_signal(
                    direction=TradeDirection.NEUTRAL,
                    confidence=0.25,
                    reasoning=reasoning,
                    indicator_values=indicator_values,
                )

        except Exception as analysis_error:
            self.logger.error(
                "Error during ADX analysis: %s",
                str(analysis_error),
                exc_info=True,
            )
            return self._create_signal(
                direction=TradeDirection.NEUTRAL,
                confidence=0.0,
                reasoning=f"ADX analysis failed due to error: {str(analysis_error)}",
                indicator_values={
                    "adx_value": None,
                    "di_positive": None,
                    "di_negative": None,
                },
            )
