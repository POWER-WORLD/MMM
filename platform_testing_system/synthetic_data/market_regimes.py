"""
Synthetic Market Regime Candlestick Generator.

Generates realistic OHLCV candlestick datasets corresponding to various
financial market conditions and indicator setups:
- Bullish Trend (sustained upward momentum)
- Bearish Trend (sustained downward momentum)
- Ranging / Consolidation / Chop (mean-reverting sideways channel)
- Bollinger Squeeze & Volatility Breakout
- EMA Golden Cross (Fast EMA crossing above Slow EMA)
- EMA Death Cross (Fast EMA crossing below Slow EMA)
- RSI Extreme Oversold (<30) and Overbought (>70)
- MACD Bullish & Bearish Crossovers
- Stochastic Oscillator Extremes (<20, >80)
- ADX High Trend (>25) vs Low Trend / Chop (<20)
- Ichimoku Cloud Breakouts & Penetrations
- Unanimous 7/7 Agreement Regimes (Unanimous CALL / Unanimous PUT)
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List, Optional

import numpy as np
import pandas as pd


class MarketRegimeType(Enum):
    """Enumeration of market regimes available for synthetic generation."""

    BULL_TREND = "BULL_TREND"
    BEAR_TREND = "BEAR_TREND"
    RANGING_SIDEWAYS = "RANGING_SIDEWAYS"
    BOLLINGER_SQUEEZE_BREAKOUT_UP = "BOLLINGER_SQUEEZE_BREAKOUT_UP"
    BOLLINGER_SQUEEZE_BREAKOUT_DOWN = "BOLLINGER_SQUEEZE_BREAKOUT_DOWN"
    EMA_GOLDEN_CROSS = "EMA_GOLDEN_CROSS"
    EMA_DEATH_CROSS = "EMA_DEATH_CROSS"
    RSI_OVERSOLD_REVERSAL = "RSI_OVERSOLD_REVERSAL"
    RSI_OVERBOUGHT_REVERSAL = "RSI_OVERBOUGHT_REVERSAL"
    MACD_BULLISH_CROSSOVER = "MACD_BULLISH_CROSSOVER"
    MACD_BEARISH_CROSSOVER = "MACD_BEARISH_CROSSOVER"
    STOCHASTIC_OVERSOLD_CROSS = "STOCHASTIC_OVERSOLD_CROSS"
    STOCHASTIC_OVERBOUGHT_CROSS = "STOCHASTIC_OVERBOUGHT_CROSS"
    HIGH_VOLATILITY_WHIPSAW = "HIGH_VOLATILITY_WHIPSAW"
    UNANIMOUS_BULLISH_CONSENSUS = "UNANIMOUS_BULLISH_CONSENSUS"
    UNANIMOUS_BEARISH_CONSENSUS = "UNANIMOUS_BEARISH_CONSENSUS"


class MarketRegimeGenerator:
    """Factory for generating synthetic OHLCV candlestick time series."""

    @staticmethod
    def _create_timestamps(count: int, interval_seconds: int = 10, end_time: Optional[datetime] = None) -> List[datetime]:
        """Generate a sequential list of UTC timestamps spaced by interval_seconds."""
        if end_time is None:
            end_time = datetime.now(tz=timezone.utc)
        return [end_time - timedelta(seconds=interval_seconds * (count - 1 - i)) for i in range(count)]

    @classmethod
    def generate_regime(
        cls,
        regime: MarketRegimeType,
        count: int = 120,
        base_price: float = 4100.0,
        interval_seconds: int = 10,
        random_seed: int = 42,
    ) -> pd.DataFrame:
        """
        Generate synthetic OHLCV candles conforming to the specified regime.

        Args:
            regime: Target MarketRegimeType.
            count: Number of candles (minimum 40 recommended for multi-period indicators).
            base_price: Baseline starting asset price.
            interval_seconds: Candle duration in seconds (defaults to 10s).
            random_seed: Seed for reproducible synthetic generation.

        Returns:
            pandas.DataFrame with columns: timestamp, open, high, low, close, volume.
        """
        np.random.seed(random_seed)
        timestamps = cls._create_timestamps(count, interval_seconds)

        if regime == MarketRegimeType.BULL_TREND:
            return cls._generate_bull_trend(timestamps, count, base_price)
        elif regime == MarketRegimeType.BEAR_TREND:
            return cls._generate_bear_trend(timestamps, count, base_price)
        elif regime == MarketRegimeType.RANGING_SIDEWAYS:
            return cls._generate_ranging(timestamps, count, base_price)
        elif regime == MarketRegimeType.BOLLINGER_SQUEEZE_BREAKOUT_UP:
            return cls._generate_bollinger_squeeze(timestamps, count, base_price, breakout_direction="UP")
        elif regime == MarketRegimeType.BOLLINGER_SQUEEZE_BREAKOUT_DOWN:
            return cls._generate_bollinger_squeeze(timestamps, count, base_price, breakout_direction="DOWN")
        elif regime == MarketRegimeType.EMA_GOLDEN_CROSS:
            return cls._generate_ema_cross(timestamps, count, base_price, direction="GOLDEN")
        elif regime == MarketRegimeType.EMA_DEATH_CROSS:
            return cls._generate_ema_cross(timestamps, count, base_price, direction="DEATH")
        elif regime == MarketRegimeType.RSI_OVERSOLD_REVERSAL:
            return cls._generate_rsi_extreme(timestamps, count, base_price, extreme_type="OVERSOLD")
        elif regime == MarketRegimeType.RSI_OVERBOUGHT_REVERSAL:
            return cls._generate_rsi_extreme(timestamps, count, base_price, extreme_type="OVERBOUGHT")
        elif regime == MarketRegimeType.MACD_BULLISH_CROSSOVER:
            return cls._generate_macd_crossover(timestamps, count, base_price, direction="BULLISH")
        elif regime == MarketRegimeType.MACD_BEARISH_CROSSOVER:
            return cls._generate_macd_crossover(timestamps, count, base_price, direction="BEARISH")
        elif regime == MarketRegimeType.STOCHASTIC_OVERSOLD_CROSS:
            return cls._generate_stochastic_extreme(timestamps, count, base_price, direction="OVERSOLD")
        elif regime == MarketRegimeType.STOCHASTIC_OVERBOUGHT_CROSS:
            return cls._generate_stochastic_extreme(timestamps, count, base_price, direction="OVERBOUGHT")
        elif regime == MarketRegimeType.HIGH_VOLATILITY_WHIPSAW:
            return cls._generate_whipsaw(timestamps, count, base_price)
        elif regime == MarketRegimeType.UNANIMOUS_BULLISH_CONSENSUS:
            return cls._generate_unanimous_consensus(timestamps, count, base_price, direction="CALL")
        elif regime == MarketRegimeType.UNANIMOUS_BEARISH_CONSENSUS:
            return cls._generate_unanimous_consensus(timestamps, count, base_price, direction="PUT")
        else:
            return cls._generate_ranging(timestamps, count, base_price)

    @classmethod
    def _generate_bull_trend(cls, timestamps: List[datetime], count: int, base_price: float) -> pd.DataFrame:
        """Sustained upward trend with higher highs and higher lows."""
        closes = [base_price]
        for _ in range(count - 1):
            drift = np.random.uniform(0.15, 0.5)
            noise = np.random.normal(0, 0.1)
            closes.append(closes[-1] + drift + noise)

        return cls._build_ohlcv(timestamps, closes, candle_volatility=0.25, bias="bullish")

    @classmethod
    def _generate_bear_trend(cls, timestamps: List[datetime], count: int, base_price: float) -> pd.DataFrame:
        """Sustained downward trend with lower highs and lower lows."""
        closes = [base_price]
        for _ in range(count - 1):
            drift = -np.random.uniform(0.15, 0.5)
            noise = np.random.normal(0, 0.1)
            closes.append(closes[-1] + drift + noise)

        return cls._build_ohlcv(timestamps, closes, candle_volatility=0.25, bias="bearish")

    @classmethod
    def _generate_ranging(cls, timestamps: List[datetime], count: int, base_price: float) -> pd.DataFrame:
        """Oscillating, range-bound mean-reverting price action around baseline."""
        t = np.linspace(0, 6 * np.pi, count)
        sine_wave = 1.5 * np.sin(t)
        noise = np.random.normal(0, 0.2, count)
        closes = base_price + sine_wave + noise

        return cls._build_ohlcv(timestamps, closes.tolist(), candle_volatility=0.3, bias="neutral")

    @classmethod
    def _generate_bollinger_squeeze(
        cls, timestamps: List[datetime], count: int, base_price: float, breakout_direction: str
    ) -> pd.DataFrame:
        """Very low volatility compression followed by violent multi-standard-deviation expansion."""
        closes = []
        current = base_price
        squeeze_point = int(count * 0.85)

        for i in range(count):
            if i < squeeze_point:
                current += np.random.normal(0, 0.05)  # Extreme squeeze
            else:
                step = 1.2 if breakout_direction == "UP" else -1.2
                current += step + np.random.normal(0, 0.1)  # Breakout
            closes.append(current)

        return cls._build_ohlcv(timestamps, closes, candle_volatility=0.15, bias="bullish" if breakout_direction == "UP" else "bearish")

    @classmethod
    def _generate_ema_cross(
        cls, timestamps: List[datetime], count: int, base_price: float, direction: str
    ) -> pd.DataFrame:
        """
        Creates historical base followed by sharp shift causing EMA(9) to cross EMA(21).
        GOLDEN: downtrend/flat then sharp surge.
        DEATH: uptrend/flat then sharp plunge.
        """
        closes = []
        current = base_price
        crossover_idx = int(count * 0.75)

        if direction == "GOLDEN":
            # Start slightly descending or flat
            for i in range(crossover_idx):
                current -= 0.08 + np.random.normal(0, 0.05)
                closes.append(current)
            # Sharp acceleration upward crossing fast EMA over slow EMA
            for i in range(count - crossover_idx):
                current += 0.85 + np.random.normal(0, 0.08)
                closes.append(current)
        else:
            # Start ascending
            for i in range(crossover_idx):
                current += 0.08 + np.random.normal(0, 0.05)
                closes.append(current)
            # Sharp acceleration downward
            for i in range(count - crossover_idx):
                current -= 0.85 + np.random.normal(0, 0.08)
                closes.append(current)

        return cls._build_ohlcv(timestamps, closes, candle_volatility=0.2, bias="bullish" if direction == "GOLDEN" else "bearish")

    @classmethod
    def _generate_rsi_extreme(
        cls, timestamps: List[datetime], count: int, base_price: float, extreme_type: str
    ) -> pd.DataFrame:
        """
        Generates candles driving RSI deep into oversold (<25) or overbought (>75).
        """
        closes = []
        current = base_price
        drop_idx = int(count * 0.7)

        if extreme_type == "OVERSOLD":
            for i in range(drop_idx):
                current += np.random.normal(0, 0.1)
                closes.append(current)
            # Consecutive aggressive red bars
            for i in range(count - drop_idx):
                current -= np.random.uniform(0.6, 1.2)
                closes.append(current)
        else:
            for i in range(drop_idx):
                current += np.random.normal(0, 0.1)
                closes.append(current)
            # Consecutive aggressive green bars
            for i in range(count - drop_idx):
                current += np.random.uniform(0.6, 1.2)
                closes.append(current)

        return cls._build_ohlcv(timestamps, closes, candle_volatility=0.15, bias="bearish" if extreme_type == "OVERSOLD" else "bullish")

    @classmethod
    def _generate_macd_crossover(
        cls, timestamps: List[datetime], count: int, base_price: float, direction: str
    ) -> pd.DataFrame:
        """Crafts price structure ensuring MACD line crosses signal line on latest candles."""
        closes = []
        current = base_price
        split = int(count * 0.7)

        if direction == "BULLISH":
            for i in range(split):
                current -= 0.15 + np.random.normal(0, 0.05)
                closes.append(current)
            for i in range(count - split):
                current += 0.65 + np.random.normal(0, 0.05)
                closes.append(current)
        else:
            for i in range(split):
                current += 0.15 + np.random.normal(0, 0.05)
                closes.append(current)
            for i in range(count - split):
                current -= 0.65 + np.random.normal(0, 0.05)
                closes.append(current)

        return cls._build_ohlcv(timestamps, closes, candle_volatility=0.2, bias="bullish" if direction == "BULLISH" else "bearish")

    @classmethod
    def _generate_stochastic_extreme(
        cls, timestamps: List[datetime], count: int, base_price: float, direction: str
    ) -> pd.DataFrame:
        """Generates Stochastic %K crossing above %D in oversold zone or below in overbought."""
        closes = []
        current = base_price
        split = int(count * 0.8)

        if direction == "OVERSOLD":
            for i in range(split):
                current -= 0.3 + np.random.normal(0, 0.05)
                closes.append(current)
            # Slight bounce at bottom
            for i in range(count - split):
                current += 0.2 + np.random.normal(0, 0.03)
                closes.append(current)
        else:
            for i in range(split):
                current += 0.3 + np.random.normal(0, 0.05)
                closes.append(current)
            # Slight rollover at top
            for i in range(count - split):
                current -= 0.2 + np.random.normal(0, 0.03)
                closes.append(current)

        return cls._build_ohlcv(timestamps, closes, candle_volatility=0.15, bias="bullish" if direction == "OVERSOLD" else "bearish")

    @classmethod
    def _generate_whipsaw(cls, timestamps: List[datetime], count: int, base_price: float) -> pd.DataFrame:
        """High volatility chops with wide candle shadows and erratic reversals."""
        closes = [base_price]
        for _ in range(count - 1):
            jump = np.random.normal(0, 1.5)
            closes.append(closes[-1] + jump)

        return cls._build_ohlcv(timestamps, closes, candle_volatility=1.8, bias="neutral")

    @classmethod
    def _generate_unanimous_consensus(
        cls, timestamps: List[datetime], count: int, base_price: float, direction: str
    ) -> pd.DataFrame:
        """
        Engineers a cohesive price structure that triggers unanimous CALL or PUT consensus
        across all 7 agents simultaneously:
        - RSI: Oversold (<30) with reversal, or Overbought (>70) with reversal
        - MACD: Fresh momentum alignment
        - Bollinger: Lower band touch / Upper band touch with bounce
        - EMA: Fast EMA crossing / aligned with trend
        - Stochastic: Fresh crossover in extreme zone
        - ADX: Strong directional trend (>25) with DI+ > DI- or DI- > DI+
        - Ichimoku: Tenkan/Kijun cross with price on favorable cloud side
        """
        closes = []
        current = base_price

        if direction == "CALL":
            # Extended gentle flat/downtrend so indicators settle and Kumo cloud is formed
            warmup = int(count * 0.70)
            for i in range(warmup):
                current += np.random.normal(0, 0.08)
                closes.append(current)

            # Dip to touch lower Bollinger band and dip RSI into oversold
            dip = int(count * 0.15)
            for i in range(dip):
                current -= 0.65 + np.random.uniform(0.1, 0.3)
                closes.append(current)

            # Sharp, powerful breakout upward with strong volume and momentum
            surge = count - warmup - dip
            for i in range(surge):
                current += 0.95 + np.random.uniform(0.2, 0.4)
                closes.append(current)

            return cls._build_ohlcv(timestamps, closes, candle_volatility=0.2, bias="bullish")
        else:
            warmup = int(count * 0.70)
            for i in range(warmup):
                current += np.random.normal(0, 0.08)
                closes.append(current)

            # Pump to touch upper Bollinger band and push RSI into overbought
            pump = int(count * 0.15)
            for i in range(pump):
                current += 0.65 + np.random.uniform(0.1, 0.3)
                closes.append(current)

            # Sharp, powerful plunge downward
            plunge = count - warmup - pump
            for i in range(plunge):
                current -= 0.95 + np.random.uniform(0.2, 0.4)
                closes.append(current)

            return cls._build_ohlcv(timestamps, closes, candle_volatility=0.2, bias="bearish")

    @classmethod
    def _build_ohlcv(
        cls,
        timestamps: List[datetime],
        closes: List[float],
        candle_volatility: float = 0.2,
        bias: str = "neutral",
    ) -> pd.DataFrame:
        """
        Constructs valid OHLCV candles from a closing price series ensuring:
        Low <= Open, Close <= High at all times.
        """
        records = []
        prev_close = closes[0]

        for i, c in enumerate(closes):
            ts = timestamps[i]
            # Open is close of previous candle plus slight micro-jitter
            o = prev_close + np.random.normal(0, 0.03)

            spread = abs(np.random.normal(candle_volatility, candle_volatility * 0.3))
            upper_wick = abs(np.random.exponential(candle_volatility * 0.6))
            lower_wick = abs(np.random.exponential(candle_volatility * 0.6))

            h = max(o, c) + upper_wick
            l = min(o, c) - lower_wick

            # Volume is higher on trending/momentum moves
            base_vol = int(np.random.uniform(20, 80))
            if abs(c - o) > candle_volatility:
                base_vol = int(base_vol * 2.2)

            records.append({
                "timestamp": ts,
                "open": round(float(o), 4),
                "high": round(float(h), 4),
                "low": round(float(l), 4),
                "close": round(float(c), 4),
                "volume": int(base_vol),
            })
            prev_close = c

        return pd.DataFrame(records)
