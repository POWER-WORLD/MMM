"""
Candle Builder Module for Gold Trading Analysis Platform.

Aggregates raw price ticks into fixed-interval OHLCV candles (default 10
seconds). Each completed candle is delivered to a user-supplied callback
for downstream consumption (storage, analysis, visualisation).

Tick timestamps are aligned to candle boundaries so that all ticks within
the same boundary window contribute to a single candle.

Typical usage:
    from core.candle_builder import CandleBuilder, CandleData

    def handle_completed_candle(candle: CandleData) -> None:
        print(candle)

    builder = CandleBuilder(
        candle_interval_seconds=10,
        on_candle_complete_callback=handle_completed_candle,
    )
    builder.add_tick(timestamp=datetime.now(tz=timezone.utc), price=2345.50)
"""

import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, Optional

logger: logging.Logger = logging.getLogger(__name__)


# ======================================================================
# Data class
# ======================================================================

@dataclass
class CandleData:
    """Immutable representation of a single OHLCV candle.

    Attributes:
        timestamp: The candle's opening time, aligned to the interval
            boundary (e.g. 12:00:00, 12:00:10, …).
        open_price: The first price observed during the candle interval.
        high_price: The highest price observed during the candle interval.
        low_price: The lowest price observed during the candle interval.
        close_price: The last price observed during the candle interval.
        volume: Aggregated trade volume for the interval (always 0 for
            tick-based construction where volume is unavailable).
        tick_count: Number of individual ticks that contributed to this
            candle.
    """

    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int = 0
    tick_count: int = 0

    def to_dict(self) -> Dict:
        """Convert the candle to a plain dictionary.

        The dictionary uses platform-standard column names so it can be
        directly appended to a list that feeds ``pd.DataFrame``.

        Returns:
            A dictionary with keys: timestamp, open, high, low, close,
            volume, tick_count.
        """
        return {
            "timestamp": self.timestamp,
            "open": self.open_price,
            "high": self.high_price,
            "low": self.low_price,
            "close": self.close_price,
            "volume": self.volume,
            "tick_count": self.tick_count,
        }


# ======================================================================
# Candle builder
# ======================================================================

class CandleBuilder:
    """Builds fixed-interval OHLCV candles from streaming price ticks.

    Incoming ticks are bucketed by their *aligned* timestamp (floored to the
    nearest candle boundary).  When a tick arrives whose aligned timestamp
    differs from the current candle's, the in-progress candle is finalized,
    delivered via callback, and a fresh candle is started.

    Thread-safety is ensured through a ``threading.Lock`` that guards all
    mutable state.

    Attributes:
        _candle_interval_seconds: The duration of each candle in seconds.
        _on_candle_complete_callback: Callable invoked with a completed
            ``CandleData`` instance.
        _lock: Threading lock for thread-safe access.
        _current_candle_start_time: Aligned start time of the candle
            currently being built, or None if no candle is in progress.
        _current_open_price: Opening price of the current candle.
        _current_high_price: Running high of the current candle.
        _current_low_price: Running low of the current candle.
        _current_close_price: Most recent price in the current candle.
        _current_volume: Accumulated volume (always 0 for raw ticks).
        _current_tick_count: Number of ticks aggregated so far.
    """

    def __init__(
        self,
        candle_interval_seconds: int,
        on_candle_complete_callback: Callable[[CandleData], None],
    ) -> None:
        """Initialize the CandleBuilder.

        Args:
            candle_interval_seconds: The fixed duration in seconds for each
                candle (e.g. 10 for 10-second candles).
            on_candle_complete_callback: A callable that receives a
                ``CandleData`` instance whenever a candle is finalized.
        """
        self._candle_interval_seconds: int = candle_interval_seconds
        self._on_candle_complete_callback: Callable[[CandleData], None] = (
            on_candle_complete_callback
        )

        self._lock: threading.Lock = threading.Lock()

        # Current (partial) candle state
        self._current_candle_start_time: Optional[datetime] = None
        self._current_open_price: float = 0.0
        self._current_high_price: float = 0.0
        self._current_low_price: float = 0.0
        self._current_close_price: float = 0.0
        self._current_volume: int = 0
        self._current_tick_count: int = 0

    def set_interval(self, new_interval_seconds: int) -> None:
        """Update the candle aggregation interval dynamically.

        Args:
            new_interval_seconds: New candle interval duration in seconds
                (e.g., 5, 10, 15, 30, 60).
        """
        with self._lock:
            if new_interval_seconds <= 0 or new_interval_seconds == self._candle_interval_seconds:
                return
            if self._current_candle_start_time is not None:
                self._finalize_candle()
            self._candle_interval_seconds = new_interval_seconds
            logger.info("CandleBuilder interval updated to %d seconds.", new_interval_seconds)

    def get_interval(self) -> int:
        """Return the current candle interval in seconds."""
        with self._lock:
            return self._candle_interval_seconds

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def add_tick(self, timestamp: datetime, price: float) -> None:
        """Ingest a single price tick and update the current candle.

        If the tick belongs to a new candle period (its aligned start time
        differs from the current candle's start time), the current candle
        is finalized first and then a new candle is begun.

        Args:
            timestamp: The UTC datetime of the price observation.
            price: The observed gold price.
        """
        aligned_start_time: datetime = self._get_candle_start_time(timestamp)

        with self._lock:
            # ---- First ever tick ----
            if self._current_candle_start_time is None:
                self._start_new_candle(aligned_start_time, price)
                return

            # ---- Tick belongs to a new candle period ----
            if aligned_start_time != self._current_candle_start_time:
                self._finalize_candle()
                self._start_new_candle(aligned_start_time, price)
                return

            # ---- Tick extends the current candle ----
            self._current_high_price = max(self._current_high_price, price)
            self._current_low_price = min(self._current_low_price, price)
            self._current_close_price = price
            self._current_tick_count += 1

    def get_current_partial_candle(self) -> Optional[Dict]:
        """Return the candle currently being built, if any.

        Returns:
            A dictionary with platform-standard column names representing
            the in-progress candle, or None if no candle is being built.
        """
        with self._lock:
            if self._current_candle_start_time is None:
                return None

            partial_candle = CandleData(
                timestamp=self._current_candle_start_time,
                open_price=self._current_open_price,
                high_price=self._current_high_price,
                low_price=self._current_low_price,
                close_price=self._current_close_price,
                volume=self._current_volume,
                tick_count=self._current_tick_count,
            )
            return partial_candle.to_dict()

    # ------------------------------------------------------------------
    # Internal methods
    # ------------------------------------------------------------------

    def _finalize_candle(self) -> None:
        """Finalize the current candle and invoke the completion callback.

        Packages the accumulated OHLCV state into a ``CandleData`` instance,
        resets the internal state, and delivers the candle to the registered
        callback.

        This method **must** be called while the caller holds ``self._lock``.
        """
        if self._current_candle_start_time is None:
            return

        completed_candle = CandleData(
            timestamp=self._current_candle_start_time,
            open_price=self._current_open_price,
            high_price=self._current_high_price,
            low_price=self._current_low_price,
            close_price=self._current_close_price,
            volume=self._current_volume,
            tick_count=self._current_tick_count,
        )

        logger.debug(
            "Candle finalized — start=%s, O=%.4f, H=%.4f, L=%.4f, C=%.4f, ticks=%d",
            completed_candle.timestamp.isoformat(),
            completed_candle.open_price,
            completed_candle.high_price,
            completed_candle.low_price,
            completed_candle.close_price,
            completed_candle.tick_count,
        )

        # Reset state before invoking callback to avoid holding stale data
        # if the callback raises.
        self._current_candle_start_time = None
        self._current_open_price = 0.0
        self._current_high_price = 0.0
        self._current_low_price = 0.0
        self._current_close_price = 0.0
        self._current_volume = 0
        self._current_tick_count = 0

        try:
            self._on_candle_complete_callback(completed_candle)
        except Exception:
            logger.exception(
                "Exception in on_candle_complete_callback for candle at %s.",
                completed_candle.timestamp.isoformat(),
            )

    def _start_new_candle(self, aligned_start_time: datetime, price: float) -> None:
        """Begin accumulating a new candle starting from the given tick.

        This method **must** be called while the caller holds ``self._lock``.

        Args:
            aligned_start_time: The boundary-aligned start time for the
                new candle.
            price: The first price tick for the new candle.
        """
        self._current_candle_start_time = aligned_start_time
        self._current_open_price = price
        self._current_high_price = price
        self._current_low_price = price
        self._current_close_price = price
        self._current_volume = 0
        self._current_tick_count = 1

        logger.debug(
            "New candle started — start=%s, price=%.4f",
            aligned_start_time.isoformat(),
            price,
        )

    def _get_candle_start_time(self, timestamp: datetime) -> datetime:
        """Align a timestamp to the nearest preceding candle boundary.

        Candle boundaries fall on exact multiples of the candle interval
        relative to the start of the minute / hour.  For a 10-second
        interval the boundaries within any minute are :00, :10, :20, :30,
        :40, :50.

        Args:
            timestamp: The raw tick timestamp to align.

        Returns:
            A new datetime whose seconds component has been floored to the
            nearest candle boundary, with microseconds zeroed.
        """
        total_epoch_seconds: int = int(timestamp.timestamp())
        aligned_epoch_seconds: int = (
            total_epoch_seconds
            - (total_epoch_seconds % self._candle_interval_seconds)
        )
        aligned_datetime: datetime = datetime.fromtimestamp(
            aligned_epoch_seconds, tz=timezone.utc
        )
        return aligned_datetime
