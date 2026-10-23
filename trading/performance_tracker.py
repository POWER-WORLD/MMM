"""
Performance Tracking Module for Gold Trading Analysis Platform.

This module provides comprehensive performance tracking and statistical
analysis for the trading platform. It records all settled trades and
calculates metrics including win rates, streaks, hourly breakdowns,
and cumulative profit/loss.

Classes:
    PerformanceTracker: Thread-safe trading performance tracker and
        statistics calculator.
"""

import threading
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional


class PerformanceTracker:
    """Thread-safe trading performance tracker and statistics calculator.

    Maintains an internal record of all settled trades and provides
    on-demand calculation of comprehensive performance metrics. All
    public methods are thread-safe through internal locking.

    Tracked Metrics:
        - Total trades, wins, and losses
        - Success rate (win percentage)
        - Cumulative profit and loss
        - Current balance and return percentage
        - Longest win and loss streaks
        - Current active streak
        - Average profit per trade
        - Hourly performance breakdown

    Args:
        initial_balance: Starting demo account balance in USD, used
            as the baseline for return percentage calculations.

    Example:
        >>> tracker = PerformanceTracker(initial_balance=10000.0)
        >>> tracker.record_trade(settled_trade_record)
        >>> statistics = tracker.get_overall_statistics()
        >>> print(f"Win Rate: {statistics['success_rate']:.1%}")
    """

    def __init__(self, initial_balance: float) -> None:
        """Initialize the performance tracker with a starting balance.

        Args:
            initial_balance: Starting demo account balance in USD.
                Used as the baseline for calculating return percentage.
        """
        self._initial_balance: float = initial_balance
        self._current_balance: float = initial_balance
        self._trade_records: List[Dict[str, Any]] = []
        self._lock: threading.Lock = threading.Lock()

    def record_trade(self, trade_record: Any) -> None:
        """Record a settled trade for performance tracking.

        Extracts relevant information from the trade record and stores
        it internally. Updates the running balance based on the trade's
        profit or loss.

        Args:
            trade_record: A settled TradeRecord instance (or any object
                with to_dictionary method or compatible attributes).
                Must have a result of 'WIN' or 'LOSS' (not 'PENDING').

        Note:
            This method is thread-safe and can be called from any thread.
        """
        with self._lock:
            if hasattr(trade_record, "to_dictionary"):
                trade_data: Dict[str, Any] = trade_record.to_dictionary()
            elif isinstance(trade_record, dict):
                trade_data = dict(trade_record)
            else:
                trade_data = {
                    "trade_id": getattr(trade_record, "trade_id", "unknown"),
                    "direction": getattr(trade_record, "direction", "unknown"),
                    "entry_price": getattr(trade_record, "entry_price", 0.0),
                    "entry_time": getattr(
                        trade_record, "entry_time", datetime.now()
                    ),
                    "exit_price": getattr(trade_record, "exit_price", 0.0),
                    "exit_time": getattr(
                        trade_record, "exit_time", datetime.now()
                    ),
                    "duration_seconds": getattr(
                        trade_record, "duration_seconds", 0
                    ),
                    "amount": getattr(trade_record, "amount", 0.0),
                    "result": getattr(trade_record, "result", "UNKNOWN"),
                    "profit_loss": getattr(trade_record, "profit_loss", 0.0),
                    "agent_signals": getattr(
                        trade_record, "agent_signals", []
                    ),
                    "payout_percentage": getattr(
                        trade_record, "payout_percentage", 0.0
                    ),
                }

            if isinstance(trade_data.get("entry_time"), datetime):
                trade_data["entry_time"] = trade_data["entry_time"].isoformat()
            if isinstance(trade_data.get("exit_time"), datetime):
                trade_data["exit_time"] = trade_data["exit_time"].isoformat()

            self._current_balance += trade_data.get("profit_loss", 0.0)
            self._trade_records.append(trade_data)

    def get_overall_statistics(self) -> Dict[str, Any]:
        """Calculate and return comprehensive trading performance statistics.

        Computes all performance metrics on demand from the recorded
        trade history. This ensures statistics are always current and
        accurate.

        Returns:
            Dictionary containing the following keys:
                - total_trades (int): Total number of settled trades.
                - winning_trades (int): Number of winning trades.
                - losing_trades (int): Number of losing trades.
                - success_rate (float): Win rate as a decimal (0.0 to 1.0).
                - total_profit_loss (float): Cumulative P&L in USD.
                - current_balance (float): Current account balance in USD.
                - initial_balance (float): Starting balance in USD.
                - return_percentage (float): Return on initial balance
                    as a decimal (e.g., 0.05 for 5% return).
                - longest_win_streak (int): Maximum consecutive wins.
                - longest_loss_streak (int): Maximum consecutive losses.
                - current_streak (dict): Current streak with 'type'
                    ('WIN', 'LOSS', or 'NONE') and 'count' keys.
                - average_profit_per_trade (float): Mean P&L per trade
                    in USD.

        Note:
            This method is thread-safe and can be called from any thread.
        """
        with self._lock:
            total_trades: int = len(self._trade_records)

            if total_trades == 0:
                return self._build_empty_statistics()

            winning_trades: int = sum(
                1
                for trade in self._trade_records
                if trade.get("result") == "WIN"
            )
            losing_trades: int = sum(
                1
                for trade in self._trade_records
                if trade.get("result") == "LOSS"
            )

            success_rate: float = (
                winning_trades / total_trades if total_trades > 0 else 0.0
            )

            total_profit_loss: float = sum(
                trade.get("profit_loss", 0.0) for trade in self._trade_records
            )

            average_profit_per_trade: float = (
                total_profit_loss / total_trades if total_trades > 0 else 0.0
            )

            return_percentage: float = (
                (self._current_balance - self._initial_balance)
                / self._initial_balance
                if self._initial_balance > 0
                else 0.0
            )

            longest_win_streak: int = self._calculate_longest_streak("WIN")
            longest_loss_streak: int = self._calculate_longest_streak("LOSS")
            current_streak: Dict[str, Any] = self._calculate_current_streak()

            return {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "success_rate": success_rate,
                "total_profit_loss": round(total_profit_loss, 2),
                "current_balance": round(self._current_balance, 2),
                "initial_balance": self._initial_balance,
                "return_percentage": round(return_percentage, 4),
                "longest_win_streak": longest_win_streak,
                "longest_loss_streak": longest_loss_streak,
                "current_streak": current_streak,
                "average_profit_per_trade": round(average_profit_per_trade, 4),
            }

    def get_recent_trades(self, count: int = 20) -> List[Dict[str, Any]]:
        """Retrieve the most recent trade records.

        Returns a list of trade record dictionaries in reverse
        chronological order (newest first).

        Args:
            count: Maximum number of recent trades to return.
                Defaults to 20.

        Returns:
            List of trade record dictionaries, ordered from newest
            to oldest, with at most 'count' entries.

        Note:
            This method is thread-safe and can be called from any thread.
        """
        with self._lock:
            recent_trades: List[Dict[str, Any]] = list(
                reversed(self._trade_records[-count:])
            )
            return recent_trades

    def get_hourly_performance(self) -> Dict[str, Any]:
        """Calculate trading performance broken down by hour of the day.

        Analyzes all recorded trades and groups them by the hour they
        were entered (0-23). For each hour that has trades, calculates
        the total trades, wins, losses, win rate, and net profit/loss.

        Returns:
            Dictionary with hour strings ("0" through "23") as keys.
            Each value is a dictionary containing:
                - total_trades (int): Number of trades entered in that hour.
                - winning_trades (int): Number of wins in that hour.
                - losing_trades (int): Number of losses in that hour.
                - success_rate (float): Win rate as decimal for that hour.
                - net_profit_loss (float): Cumulative P&L for that hour.

        Note:
            This method is thread-safe and can be called from any thread.
            Hours with no trades are omitted from the result.
        """
        with self._lock:
            hourly_data: Dict[str, Dict[str, Any]] = defaultdict(
                lambda: {
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "success_rate": 0.0,
                    "net_profit_loss": 0.0,
                }
            )

            for trade in self._trade_records:
                entry_time_value = trade.get("entry_time")
                if entry_time_value is None:
                    continue

                if isinstance(entry_time_value, str):
                    try:
                        parsed_time = datetime.fromisoformat(entry_time_value)
                        trade_hour: int = parsed_time.hour
                    except (ValueError, TypeError):
                        continue
                elif isinstance(entry_time_value, datetime):
                    trade_hour = entry_time_value.hour
                else:
                    continue

                hour_key: str = str(trade_hour)
                hourly_data[hour_key]["total_trades"] += 1

                trade_result: str = trade.get("result", "")
                if trade_result == "WIN":
                    hourly_data[hour_key]["winning_trades"] += 1
                elif trade_result == "LOSS":
                    hourly_data[hour_key]["losing_trades"] += 1

                hourly_data[hour_key]["net_profit_loss"] += trade.get(
                    "profit_loss", 0.0
                )

            for hour_key in hourly_data:
                hour_total: int = hourly_data[hour_key]["total_trades"]
                hour_wins: int = hourly_data[hour_key]["winning_trades"]
                hourly_data[hour_key]["success_rate"] = (
                    hour_wins / hour_total if hour_total > 0 else 0.0
                )
                hourly_data[hour_key]["net_profit_loss"] = round(
                    hourly_data[hour_key]["net_profit_loss"], 2
                )

            return dict(hourly_data)

    def _build_empty_statistics(self) -> Dict[str, Any]:
        """Build a statistics dictionary with zero/default values.

        Used when no trades have been recorded yet.

        Returns:
            Dictionary with all statistics keys set to zero or
            default values.
        """
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "success_rate": 0.0,
            "total_profit_loss": 0.0,
            "current_balance": round(self._current_balance, 2),
            "initial_balance": self._initial_balance,
            "return_percentage": 0.0,
            "longest_win_streak": 0,
            "longest_loss_streak": 0,
            "current_streak": {"type": "NONE", "count": 0},
            "average_profit_per_trade": 0.0,
        }

    def _calculate_longest_streak(self, streak_type: str) -> int:
        """Calculate the longest consecutive streak of a given result type.

        Iterates through all trade records and finds the maximum number
        of consecutive trades with the specified result.

        Args:
            streak_type: The result type to track ('WIN' or 'LOSS').

        Returns:
            The length of the longest consecutive streak of the
            specified type. Returns 0 if no trades of that type exist.
        """
        longest_streak: int = 0
        current_count: int = 0

        for trade in self._trade_records:
            if trade.get("result") == streak_type:
                current_count += 1
                longest_streak = max(longest_streak, current_count)
            else:
                current_count = 0

        return longest_streak

    def _calculate_current_streak(self) -> Dict[str, Any]:
        """Calculate the current active streak from the most recent trades.

        Counts consecutive trades of the same result working backwards
        from the most recent trade.

        Returns:
            Dictionary with:
                - type (str): 'WIN', 'LOSS', or 'NONE' if no trades.
                - count (int): Number of consecutive trades in the
                    current streak.
        """
        if not self._trade_records:
            return {"type": "NONE", "count": 0}

        most_recent_result: str = self._trade_records[-1].get("result", "NONE")
        streak_count: int = 0

        for trade in reversed(self._trade_records):
            if trade.get("result") == most_recent_result:
                streak_count += 1
            else:
                break

        return {"type": most_recent_result, "count": streak_count}
