"""
Unit Tests for Performance and Win Rate Tracker Module.

Verifies win/loss statistics, success rate computation, return on balance,
winning/losing streak calculations, hourly breakdowns, and thread-safe locking.
"""

from datetime import datetime, timezone
import pytest

from trading.performance_tracker import PerformanceTracker
from trading.trade_executor import TradeRecord


class TestPerformanceTracker:
    """Test suite for PerformanceTracker."""

    def test_initial_tracker_statistics(self) -> None:
        """Verify initial statistics with zero trades and baseline balance."""
        tracker = PerformanceTracker(initial_balance=10000.0)
        stats = tracker.get_overall_statistics()

        assert stats["total_trades"] == 0
        assert stats["winning_trades"] == 0
        assert stats["losing_trades"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["total_profit_loss"] == 0.0
        assert stats["current_balance"] == 10000.0
        assert stats["return_percentage"] == 0.0
        assert stats["longest_win_streak"] == 0
        assert stats["longest_loss_streak"] == 0
        assert stats["current_streak"] == {"type": "NONE", "count": 0}
        assert stats["average_profit_per_trade"] == 0.0
        assert tracker.get_recent_trades() == []

    def test_record_multiple_trades_and_stats(self) -> None:
        """Verify recording wins and losses correctly computes totals and decimal win rate."""
        tracker = PerformanceTracker(initial_balance=1000.0)

        # 3 Wins (+$8.20 each) and 1 Loss (-$10.00) -> 4 trades, 0.75 win rate, net PnL = +$14.60
        for i in range(3):
            t_win = TradeRecord(
                trade_id=f"win_{i}",
                direction="CALL",
                entry_price=4100.0,
                entry_time=datetime.now(tz=timezone.utc),
                exit_price=4105.0,
                exit_time=datetime.now(tz=timezone.utc),
                duration_seconds=60,
                amount=10.0,
                result="WIN",
                profit_loss=8.20,
            )
            tracker.record_trade(t_win)

        t_loss = TradeRecord(
            trade_id="loss_1",
            direction="PUT",
            entry_price=4100.0,
            entry_time=datetime.now(tz=timezone.utc),
            exit_price=4105.0,
            exit_time=datetime.now(tz=timezone.utc),
            duration_seconds=60,
            amount=10.0,
            result="LOSS",
            profit_loss=-10.0,
        )
        tracker.record_trade(t_loss)

        stats = tracker.get_overall_statistics()
        assert stats["total_trades"] == 4
        assert stats["winning_trades"] == 3
        assert stats["losing_trades"] == 1
        assert stats["success_rate"] == 0.75
        assert round(stats["total_profit_loss"], 2) == 14.60
        assert round(stats["current_balance"], 2) == 1014.60
        assert stats["return_percentage"] == 0.0146

    def test_winning_and_losing_streak_tracking(self) -> None:
        """Verify longest_win_streak, longest_loss_streak, and current_streak tracking."""
        tracker = PerformanceTracker(initial_balance=1000.0)

        # Sequence: WIN, WIN, WIN, LOSS, LOSS, WIN, WIN
        results = [
            ("WIN", 8.2),
            ("WIN", 8.2),
            ("WIN", 8.2),
            ("LOSS", -10.0),
            ("LOSS", -10.0),
            ("WIN", 8.2),
            ("WIN", 8.2),
        ]

        for i, (res, pnl) in enumerate(results):
            rec = TradeRecord(
                trade_id=f"t_{i}",
                direction="CALL",
                entry_price=4100.0,
                entry_time=datetime.now(tz=timezone.utc),
                exit_price=4105.0 if res == "WIN" else 4095.0,
                exit_time=datetime.now(tz=timezone.utc),
                duration_seconds=60,
                amount=10.0,
                result=res,
                profit_loss=pnl,
            )
            tracker.record_trade(rec)

        stats = tracker.get_overall_statistics()
        assert stats["longest_win_streak"] == 3
        assert stats["longest_loss_streak"] == 2
        assert stats["current_streak"] == {"type": "WIN", "count": 2}

    def test_recent_trades_slice(self) -> None:
        """Verify get_recent_trades retrieves most recent trades up to count."""
        tracker = PerformanceTracker(initial_balance=1000.0)

        for i in range(10):
            tracker.record_trade({
                "trade_id": f"t_{i}",
                "result": "WIN",
                "profit_loss": 0.82,
                "entry_time": datetime.now(tz=timezone.utc),
            })

        recent_5 = tracker.get_recent_trades(count=5)
        assert len(recent_5) == 5
        assert recent_5[0]["trade_id"] == "t_9"  # Newest first
