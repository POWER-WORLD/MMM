"""
Thread-Safe In-Memory Data Store Module for Gold Trading Analysis Platform.

Provides the ``PlatformDataStore`` class — a centralised, thread-safe
repository for all runtime data: completed OHLCV candles, the latest
spot price, trade execution records, and agent consensus signals.

Every public method is guarded by a ``threading.RLock`` so the store can be
safely accessed from the price-polling thread, candle-building callbacks,
the analysis pipeline, and the web dashboard simultaneously.

Typical usage:
    from core.data_store import PlatformDataStore

    store = PlatformDataStore(max_candles=4320)
    store.add_candle({"timestamp": ..., "open": ..., ...})
    df = store.get_candles_dataframe(count=100)
"""

import logging
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import pandas as pd

logger: logging.Logger = logging.getLogger(__name__)


class PlatformDataStore:
    """Thread-safe in-memory data store for the trading platform.

    Stores completed candles, live price state, executed trades, and the
    latest agent signals.  Access to every internal collection is serialised
    through a reentrant lock (``threading.RLock``).

    Attributes:
        _max_candles: Maximum number of candles retained in memory.
        _lock: Reentrant lock protecting all mutable state.
        _candles: Ordered list of candle dictionaries (oldest first).
        _current_price: Most recently observed spot price.
        _current_price_timestamp: Timestamp of the most recent spot price.
        _trade_records: Complete list of trade dictionaries.
        _agent_signals: Most recent set of agent consensus signals.
    """

    def __init__(self, max_candles: int) -> None:
        """Initialize the PlatformDataStore.

        Args:
            max_candles: The maximum number of completed candles to keep
                in memory.  When this limit is exceeded the oldest candles
                are discarded.
        """
        self._max_candles: int = max_candles
        self._lock: threading.RLock = threading.RLock()

        # Candle storage
        self._candles: List[Dict] = []

        # Live price
        self._current_price: Optional[float] = None
        self._current_price_timestamp: Optional[datetime] = None

        # Trade records
        self._trade_records: List[Dict] = []

        # Agent signals
        self._agent_signals: List[Dict] = []

        logger.info(
            "PlatformDataStore initialized — max_candles=%d",
            self._max_candles,
        )

    # ------------------------------------------------------------------
    # Candle management
    # ------------------------------------------------------------------

    def add_candle(self, candle_data: Dict) -> None:
        """Append a completed candle and trim the collection if necessary.

        Args:
            candle_data: A dictionary with platform-standard keys
                (timestamp, open, high, low, close, volume, tick_count).
        """
        with self._lock:
            self._candles.append(candle_data)

            excess_count: int = len(self._candles) - self._max_candles
            if excess_count > 0:
                self._candles = self._candles[excess_count:]
                logger.debug(
                    "Trimmed %d oldest candle(s) — store size=%d",
                    excess_count,
                    len(self._candles),
                )

            logger.debug(
                "Candle added — total candles in store=%d",
                len(self._candles),
            )

    def get_candles_dataframe(self, count: Optional[int] = None) -> pd.DataFrame:
        """Return stored candles as a pandas DataFrame.

        A new DataFrame is constructed on every call so that callers receive
        an independent copy that will not be affected by concurrent writes.

        Args:
            count: Optional number of most-recent candles to return.
                If None or greater than the available count, all candles
                are returned.

        Returns:
            A pandas DataFrame with columns matching the candle dict keys.
            Returns an empty DataFrame (with no columns) if no candles
            are stored.
        """
        with self._lock:
            if not self._candles:
                return pd.DataFrame()

            if count is not None and count > 0:
                selected_candles: List[Dict] = self._candles[-count:]
            else:
                selected_candles = list(self._candles)

        return pd.DataFrame(selected_candles)

    def get_candle_count(self) -> int:
        """Return the number of candles currently stored.

        Returns:
            Integer count of candles in the store.
        """
        with self._lock:
            return len(self._candles)

    def get_candles(self, count: Optional[int] = None) -> List[Dict]:
        """Return a copy of stored candle dictionaries.

        Args:
            count: Optional number of most-recent candles to return.

        Returns:
            List of candle dictionaries.
        """
        with self._lock:
            if count is not None and count > 0:
                return list(self._candles[-count:])
            return list(self._candles)

    def clear_candles(self) -> None:
        """Clear all stored candles from memory."""
        with self._lock:
            self._candles.clear()

    def get_latest_price(self) -> Optional[float]:
        """Return the close price of the most recent candle or latest spot price.

        Returns:
            The close price as a float, or current spot price if no candles,
            or None if no price is available.
        """
        with self._lock:
            if self._candles:
                return self._candles[-1].get("close")
            return self._current_price

    # ------------------------------------------------------------------
    # Live price
    # ------------------------------------------------------------------

    def set_current_price(self, price: float, timestamp: Optional[datetime] = None) -> None:
        """Update the latest observed spot price.

        Args:
            price: The most recent gold spot price.
            timestamp: The UTC datetime at which the price was observed (defaults to now).
        """
        with self._lock:
            self._current_price = price
            self._current_price_timestamp = timestamp or datetime.now(tz=timezone.utc)

    def get_current_price(self) -> Tuple[Optional[float], Optional[datetime]]:
        """Retrieve the latest observed spot price and its timestamp.

        Returns:
            A tuple of (price, timestamp).  Both elements are None if no
            price has been set yet.
        """
        with self._lock:
            return self._current_price, self._current_price_timestamp

    # ------------------------------------------------------------------
    # Trade records
    # ------------------------------------------------------------------

    def add_trade_record(self, trade: Dict) -> None:
        """Record a new trade execution.

        Args:
            trade: A dictionary describing the trade.  Expected keys
                include ``trade_id``, ``direction``, ``entry_price``,
                ``timestamp``, ``status``, etc.
        """
        with self._lock:
            self._trade_records.append(trade)
            logger.info(
                "Trade record added — trade_id=%s, total_trades=%d",
                trade.get("trade_id", "unknown"),
                len(self._trade_records),
            )

    def get_trade_records(self, count: Optional[int] = None) -> List[Dict]:
        """Return a copy of trade records.

        Args:
            count: Optional maximum number of recent trades to return.

        Returns:
            A list of trade dictionaries ordered by insertion time.
        """
        with self._lock:
            if count is not None and count > 0:
                return list(self._trade_records[-count:])
            return list(self._trade_records)

    def get_pending_trades(self) -> List[Dict]:
        """Return trade records whose status is ``'pending'`` or ``'active'``.

        Returns:
            A filtered list of trade dictionaries that have not yet
            been settled.
        """
        with self._lock:
            pending_statuses = {"pending", "active"}
            return [
                trade
                for trade in self._trade_records
                if trade.get("status") in pending_statuses
            ]

    def update_trade_record(self, trade_id: str, updates: Dict) -> None:
        """Apply partial updates to an existing trade record.

        Searches for the first trade whose ``trade_id`` matches the
        supplied value and merges the ``updates`` dictionary into it.

        Args:
            trade_id: The unique identifier of the trade to update.
            updates: A dictionary of fields to merge into the trade record.

        Raises:
            KeyError: If no trade with the given ``trade_id`` is found.
        """
        with self._lock:
            for trade_record in self._trade_records:
                if trade_record.get("trade_id") == trade_id:
                    trade_record.update(updates)
                    logger.info(
                        "Trade record updated — trade_id=%s, fields=%s",
                        trade_id,
                        list(updates.keys()),
                    )
                    return

            raise KeyError(
                f"Trade record with trade_id='{trade_id}' not found in data store."
            )

    # ------------------------------------------------------------------
    # Agent signals
    # ------------------------------------------------------------------

    def set_agent_signals(self, signals: List[Dict]) -> None:
        """Replace the stored agent signals with a new set.

        Args:
            signals: A list of signal dictionaries, each typically
                containing ``agent_name``, ``direction``, ``confidence``,
                and ``reasoning``.
        """
        with self._lock:
            self._agent_signals = list(signals)
            logger.debug(
                "Agent signals updated — %d signal(s) stored.",
                len(self._agent_signals),
            )

    def get_agent_signals(self) -> List[Dict]:
        """Return a copy of the most recent agent signals.

        Returns:
            A list of signal dictionaries.  Returns an empty list if no
            signals have been set.
        """
        with self._lock:
            return list(self._agent_signals)
