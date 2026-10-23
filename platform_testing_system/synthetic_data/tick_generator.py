"""
Synthetic Price Tick Stream Generator.

Produces granular, high-frequency price tick streams with millisecond-accurate
timestamps for testing price polling, candle construction, and data store buffering.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Iterator, List, Optional, Tuple

import numpy as np


class TickPatternType(Enum):
    """Enumeration of tick stream patterns."""

    GEOMETRIC_BROWNIAN_MOTION = "GEOMETRIC_BROWNIAN_MOTION"
    STEADY_UPWARD_DRIFT = "STEADY_UPWARD_DRIFT"
    STEADY_DOWNWARD_DRIFT = "STEADY_DOWNWARD_DRIFT"
    JUMP_DIFFUSION = "JUMP_DIFFUSION"
    FLASH_CRASH_RECOVERY = "FLASH_CRASH_RECOVERY"
    HIGH_FREQUENCY_BURST = "HIGH_FREQUENCY_BURST"
    OUT_OF_ORDER_TIMESTAMPS = "OUT_OF_ORDER_TIMESTAMPS"


@dataclass(frozen=True)
class PriceTick:
    """Individual price tick observation."""

    timestamp: datetime
    price: float
    volume: float = 1.0


class PriceTickGenerator:
    """Generator for streaming synthetic financial price ticks."""

    @classmethod
    def generate_ticks(
        cls,
        pattern: TickPatternType = TickPatternType.GEOMETRIC_BROWNIAN_MOTION,
        duration_seconds: float = 60.0,
        ticks_per_second: float = 5.0,
        start_price: float = 4100.0,
        start_time: Optional[datetime] = None,
        random_seed: int = 42,
    ) -> List[PriceTick]:
        """
        Generate a batch of PriceTick objects according to the chosen pattern.

        Args:
            pattern: Target TickPatternType.
            duration_seconds: Total time span of the tick stream.
            ticks_per_second: Frequency of price observations.
            start_price: Starting asset price.
            start_time: Starting UTC datetime (defaults to current UTC).
            random_seed: Random seed for reproducible streams.

        Returns:
            List of PriceTick objects.
        """
        np.random.seed(random_seed)
        if start_time is None:
            start_time = datetime.now(tz=timezone.utc)

        total_ticks = int(duration_seconds * ticks_per_second)
        dt_seconds = 1.0 / ticks_per_second

        timestamps = [
            start_time + timedelta(seconds=i * dt_seconds)
            for i in range(total_ticks)
        ]

        if pattern == TickPatternType.STEADY_UPWARD_DRIFT:
            prices = cls._simulate_drift(total_ticks, start_price, drift=0.08, vol=0.03)
        elif pattern == TickPatternType.STEADY_DOWNWARD_DRIFT:
            prices = cls._simulate_drift(total_ticks, start_price, drift=-0.08, vol=0.03)
        elif pattern == TickPatternType.JUMP_DIFFUSION:
            prices = cls._simulate_jump_diffusion(total_ticks, start_price)
        elif pattern == TickPatternType.FLASH_CRASH_RECOVERY:
            prices = cls._simulate_flash_crash(total_ticks, start_price)
        elif pattern == TickPatternType.HIGH_FREQUENCY_BURST:
            prices = cls._simulate_drift(total_ticks, start_price, drift=0.0, vol=0.05)
        elif pattern == TickPatternType.OUT_OF_ORDER_TIMESTAMPS:
            prices = cls._simulate_drift(total_ticks, start_price, drift=0.01, vol=0.05)
            # Permute a fraction of timestamps to simulate network packet reordering
            swap_count = max(1, total_ticks // 15)
            for _ in range(swap_count):
                idx = np.random.randint(1, total_ticks - 1)
                timestamps[idx], timestamps[idx + 1] = timestamps[idx + 1], timestamps[idx]
        else:
            # Default Geometric Brownian Motion
            prices = cls._simulate_drift(total_ticks, start_price, drift=0.0, vol=0.06)

        return [
            PriceTick(timestamp=ts, price=round(float(p), 4))
            for ts, p in zip(timestamps, prices)
        ]

    @classmethod
    def stream_ticks(
        cls,
        pattern: TickPatternType = TickPatternType.GEOMETRIC_BROWNIAN_MOTION,
        duration_seconds: float = 60.0,
        ticks_per_second: float = 5.0,
        start_price: float = 4100.0,
        random_seed: int = 42,
    ) -> Iterator[PriceTick]:
        """Generator yielding PriceTicks one by one."""
        ticks = cls.generate_ticks(
            pattern=pattern,
            duration_seconds=duration_seconds,
            ticks_per_second=ticks_per_second,
            start_price=start_price,
            random_seed=random_seed,
        )
        for tick in ticks:
            yield tick

    @staticmethod
    def _simulate_drift(count: int, start_price: float, drift: float, vol: float) -> List[float]:
        """Simulate asset price series with constant drift and Gaussian volatility."""
        prices = [start_price]
        for _ in range(count - 1):
            change = drift + np.random.normal(0, vol)
            prices.append(prices[-1] + change)
        return prices

    @staticmethod
    def _simulate_jump_diffusion(count: int, start_price: float) -> List[float]:
        """Simulate Merton jump diffusion (continuous diffusion punctuated by rare jumps)."""
        prices = [start_price]
        jump_probability = 0.05
        for _ in range(count - 1):
            normal_step = np.random.normal(0, 0.04)
            if np.random.random() < jump_probability:
                jump = np.random.choice([-1.5, 1.5]) * np.random.uniform(0.8, 2.5)
            else:
                jump = 0.0
            prices.append(prices[-1] + normal_step + jump)
        return prices

    @staticmethod
    def _simulate_flash_crash(count: int, start_price: float) -> List[float]:
        """Simulate sudden market collapse followed by rapid V-shaped recovery."""
        prices = []
        current = start_price
        crash_start = int(count * 0.40)
        bottom = int(count * 0.55)
        recovery_end = int(count * 0.75)

        for i in range(count):
            if i < crash_start:
                current += np.random.normal(0, 0.03)
            elif crash_start <= i < bottom:
                current -= np.random.uniform(0.5, 1.2)  # Plunge
            elif bottom <= i < recovery_end:
                current += np.random.uniform(0.4, 0.9)  # V-rebound
            else:
                current += np.random.normal(0, 0.04)
            prices.append(current)

        return prices
