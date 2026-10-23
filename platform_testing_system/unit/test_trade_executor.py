"""
Unit Tests for Trade Execution and 60-Second Settlement Engine.

Verifies TradeRecord serialization, placing CALL/PUT trades, maximum concurrent trade
enforcement, settlement rules (CALL WIN/LOSS, PUT WIN/LOSS), and balance accounting.
"""

from datetime import datetime
import pytest

from agents.base_agent import TradeDirection
from trading.trade_executor import TradeExecutor, TradeRecord


class TestTradeExecutor:
    """Test suite for TradeRecord and TradeExecutor."""

    def test_trade_record_to_dictionary(self) -> None:
        """Verify TradeRecord serialization to dictionary format."""
        now = datetime.now()
        rec = TradeRecord(
            trade_id="trade_12345",
            direction="CALL",
            entry_price=4100.0,
            entry_time=now,
            exit_price=4105.0,
            exit_time=now,
            duration_seconds=60,
            amount=1.0,
            result="WIN",
            profit_loss=0.82,
            agent_signals=[{"name": "RSI", "signal": "CALL"}],
            payout_percentage=0.82,
        )
        d = rec.to_dictionary()
        assert d["trade_id"] == "trade_12345"
        assert d["direction"] == "CALL"
        assert d["entry_price"] == 4100.0
        assert d["exit_price"] == 4105.0
        assert d["result"] == "WIN"
        assert d["profit_loss"] == 0.82
        assert d["payout_percentage"] == 0.82

    def test_initial_balance_and_empty_state(self) -> None:
        """Verify clean executor starts with initial balance and no pending trade."""
        executor = TradeExecutor(initial_balance=5000.0, payout_percentage=0.82)
        assert executor.current_balance == 5000.0
        assert executor.has_pending_trade() is False
        assert executor.get_pending_trade() is None

    def test_place_trade_creates_pending_record(self) -> None:
        """Verify placing a trade reserves stake and marks record as PENDING."""
        executor = TradeExecutor(initial_balance=10000.0, payout_percentage=0.82)
        trade = executor.place_trade(
            direction=TradeDirection.CALL,
            entry_price=4100.0,
            amount=10.0,
            agent_signals=[],
            duration_seconds=60,
        )

        assert trade is not None
        assert trade.result == "PENDING"
        assert trade.direction == "CALL"
        assert trade.entry_price == 4100.0
        assert trade.amount == 10.0
        assert trade.duration_seconds == 60
        assert executor.has_pending_trade() is True
        assert executor.get_pending_trade().trade_id == trade.trade_id

    def test_cannot_place_second_trade_while_one_is_pending(self) -> None:
        """Verify maximum 1 concurrent trade is enforced strictly by raising ValueError."""
        executor = TradeExecutor(initial_balance=10000.0, payout_percentage=0.82)
        trade1 = executor.place_trade(TradeDirection.CALL, 4100.0, 1.0)
        assert trade1 is not None

        # Attempting second trade while first is pending must raise ValueError
        with pytest.raises(ValueError) as excinfo:
            executor.place_trade(TradeDirection.PUT, 4105.0, 1.0)
        assert "Cannot place a new trade while another trade is pending" in str(excinfo.value)

    def test_settle_call_trade_as_win(self) -> None:
        """Verify CALL trade wins when exit_price > entry_price with 82% payout."""
        executor = TradeExecutor(initial_balance=10000.0, payout_percentage=0.82)
        trade = executor.place_trade(TradeDirection.CALL, 4100.0, 100.0)

        # Settle at 4105.0 (exit > entry)
        settled = executor.settle_trade(trade, exit_price=4105.0)
        assert settled.result == "WIN"
        assert settled.profit_loss == 82.0  # 100 * 0.82
        assert executor.current_balance == 10082.0
        assert executor.has_pending_trade() is False

    def test_settle_call_trade_as_loss(self) -> None:
        """Verify CALL trade loses when exit_price <= entry_price."""
        executor = TradeExecutor(initial_balance=10000.0, payout_percentage=0.82)
        trade = executor.place_trade(TradeDirection.CALL, 4100.0, 100.0)

        # Settle at 4095.0 (exit < entry)
        settled = executor.settle_trade(trade, exit_price=4095.0)
        assert settled.result == "LOSS"
        assert settled.profit_loss == -100.0
        assert executor.current_balance == 9900.0
        assert executor.has_pending_trade() is False

    def test_settle_put_trade_as_win(self) -> None:
        """Verify PUT trade wins when exit_price < entry_price."""
        executor = TradeExecutor(initial_balance=10000.0, payout_percentage=0.82)
        trade = executor.place_trade(TradeDirection.PUT, 4100.0, 50.0)

        # Settle at 4096.0 (exit < entry for PUT is WIN)
        settled = executor.settle_trade(trade, exit_price=4096.0)
        assert settled.result == "WIN"
        assert settled.profit_loss == 41.0  # 50 * 0.82
        assert executor.current_balance == 10041.0

    def test_settle_put_trade_as_loss(self) -> None:
        """Verify PUT trade loses when exit_price >= entry_price."""
        executor = TradeExecutor(initial_balance=10000.0, payout_percentage=0.82)
        trade = executor.place_trade(TradeDirection.PUT, 4100.0, 50.0)

        # Settle at 4103.0 (exit > entry for PUT is LOSS)
        settled = executor.settle_trade(trade, exit_price=4103.0)
        assert settled.result == "LOSS"
        assert settled.profit_loss == -50.0
        assert executor.current_balance == 9950.0
