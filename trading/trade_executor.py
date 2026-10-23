"""
Simulated Trade Execution Module for Gold Trading Analysis Platform.

This module provides a complete simulated trade execution engine for demo
accounts. It handles trade placement, settlement, and balance management
without connecting to any real brokerage or exchange.

Classes:
    TradeRecord: Immutable data container for individual trade records.
    TradeExecutor: Simulated trade execution engine for demo trading.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.base_agent import TradeDirection, TradeSignal
from config import PLATFORM_CONFIG


@dataclass
class TradeRecord:
    """Immutable data container representing a single trade record.

    Stores all relevant information about a trade including entry/exit
    prices, timing, direction, result, and the agent signals that
    contributed to the trade decision.

    Attributes:
        trade_id: Unique identifier for the trade (UUID4 string).
        direction: Trade direction as string ('CALL' or 'PUT').
        entry_price: Gold price at the time of trade entry.
        entry_time: Timestamp when the trade was placed.
        exit_price: Gold price at the time of trade settlement (None if pending).
        exit_time: Timestamp when the trade was settled (None if pending).
        duration_seconds: Expected duration of the trade in seconds.
        amount: Trade amount in USD.
        result: Current trade status ('PENDING', 'WIN', or 'LOSS').
        profit_loss: Realized profit or loss in USD (0.0 while pending).
        agent_signals: List of dictionaries summarizing each agent's signal.
        payout_percentage: Payout multiplier applied on winning trades.
    """

    trade_id: str
    direction: str
    entry_price: float
    entry_time: datetime
    exit_price: Optional[float]
    exit_time: Optional[datetime]
    duration_seconds: int
    amount: float
    result: str
    profit_loss: float
    agent_signals: List[Dict] = field(default_factory=list)
    payout_percentage: float = 0.0

    def to_dictionary(self) -> Dict:
        """Convert the trade record to a serializable dictionary.

        Returns:
            Dictionary representation of the trade record with all
            datetime objects converted to ISO format strings.
        """
        return {
            "trade_id": self.trade_id,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "entry_time": self.entry_time.isoformat() if self.entry_time else None,
            "exit_price": self.exit_price,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "duration_seconds": self.duration_seconds,
            "amount": self.amount,
            "result": self.result,
            "profit_loss": self.profit_loss,
            "agent_signals": self.agent_signals,
            "payout_percentage": self.payout_percentage,
        }


class TradeExecutor:
    """Simulated trade execution engine for demo trading accounts.

    Manages the lifecycle of simulated trades including placement,
    settlement, and balance tracking. Designed exclusively for demo
    accounts with no real money at risk.

    The executor maintains a running balance and supports one pending
    trade at a time. Trades are settled by comparing entry and exit
    prices against the trade direction.

    Settlement Rules:
        - CALL wins if exit_price > entry_price
        - PUT wins if exit_price < entry_price
        - Winning profit = amount * payout_percentage
        - Losing profit = -amount

    Attributes:
        current_balance: Current demo account balance in USD.

    Args:
        initial_balance: Starting balance for the demo account in USD.
        payout_percentage: Decimal multiplier for winning trade payouts
            (e.g., 0.82 for 82% payout).

    Example:
        >>> executor = TradeExecutor(
        ...     initial_balance=10000.0,
        ...     payout_percentage=0.82
        ... )
        >>> trade = executor.place_trade(
        ...     direction=TradeDirection.CALL,
        ...     entry_price=2650.50,
        ...     amount=1.0,
        ...     agent_signals=[]
        ... )
        >>> settled = executor.settle_trade(trade, exit_price=2651.00)
        >>> print(settled.result)  # 'WIN'
    """

    def __init__(self, initial_balance: float, payout_percentage: float) -> None:
        """Initialize the trade executor with starting balance and payout rate.

        Args:
            initial_balance: Starting balance for the demo account in USD.
            payout_percentage: Decimal multiplier for winning trade payouts
                (e.g., 0.82 means 82% return on winning trades).
        """
        self._initial_balance: float = initial_balance
        self.current_balance: float = initial_balance
        self._payout_percentage: float = payout_percentage
        self._pending_trade: Optional[TradeRecord] = None
        self._trade_history: List[TradeRecord] = []

    def place_trade(
        self,
        direction: TradeDirection,
        entry_price: float,
        amount: float = 1.0,
        agent_signals: Optional[List[Any]] = None,
        duration_seconds: int = 60,
    ) -> TradeRecord:
        """Place a new simulated trade on the demo account.

        Creates a new pending trade record with the specified parameters.
        Only one trade can be pending at a time. The trade amount is
        deducted from the current balance immediately upon placement.

        Args:
            direction: The trade direction (CALL for price up, PUT for
                price down).
            entry_price: The gold price at the time of trade entry.
            amount: The trade amount in USD to risk on this trade (defaults to 1.0).
            agent_signals: Optional list of TradeSignal objects or dicts.
            duration_seconds: Duration of the trade in seconds (defaults to 60).

        Returns:
            A new TradeRecord instance with status set to 'PENDING'.

        Raises:
            ValueError: If a trade is already pending or if the amount
                exceeds the current balance.
        """
        if self._pending_trade is not None:
            raise ValueError(
                "Cannot place a new trade while another trade is pending. "
                f"Pending trade ID: {self._pending_trade.trade_id}"
            )

        if amount > self.current_balance:
            raise ValueError(
                f"Insufficient balance for trade. "
                f"Requested amount: ${amount:.2f}, "
                f"Available balance: ${self.current_balance:.2f}"
            )

        serialized_agent_signals: List[Dict] = []
        if agent_signals is not None:
            for signal in agent_signals:
                if isinstance(signal, dict):
                    serialized_agent_signals.append(signal)
                else:
                    signal_summary: Dict = {
                        "agent_name": getattr(signal, "agent_name", "Unknown"),
                        "direction": signal.direction.value if hasattr(signal, "direction") and signal.direction else "NEUTRAL",
                        "confidence": getattr(signal, "confidence", 0.0),
                        "reasoning": getattr(signal, "reasoning", ""),
                    }
                    serialized_agent_signals.append(signal_summary)

        direction_string: str = direction.value if isinstance(direction, TradeDirection) else str(direction)

        trade_record = TradeRecord(
            trade_id=str(uuid.uuid4()),
            direction=direction_string,
            entry_price=entry_price,
            entry_time=datetime.now(),
            exit_price=None,
            exit_time=None,
            duration_seconds=duration_seconds,
            amount=amount,
            result="PENDING",
            profit_loss=0.0,
            agent_signals=serialized_agent_signals,
            payout_percentage=self._payout_percentage,
        )

        self.current_balance -= amount
        self._pending_trade = trade_record

        return trade_record

    def settle_trade(
        self, trade_record: TradeRecord, exit_price: float
    ) -> TradeRecord:
        """Settle a pending trade by comparing entry and exit prices.

        Determines the trade outcome based on the direction and price
        movement:
            - CALL wins if exit_price > entry_price (price went up)
            - PUT wins if exit_price < entry_price (price went down)
            - If prices are equal, the trade is a loss

        On a win, the profit is calculated as: amount * payout_percentage.
        On a loss, the entire trade amount is forfeited.

        Args:
            trade_record: The pending TradeRecord to settle.
            exit_price: The gold price at the time of trade settlement.

        Returns:
            An updated TradeRecord with the result, exit price, exit time,
            and profit/loss filled in.

        Raises:
            ValueError: If the provided trade record is not the current
                pending trade or has already been settled.
        """
        if self._pending_trade is None:
            raise ValueError(
                "No pending trade to settle. Place a trade first."
            )

        if trade_record.trade_id != self._pending_trade.trade_id:
            raise ValueError(
                f"Trade ID mismatch. Expected: {self._pending_trade.trade_id}, "
                f"Received: {trade_record.trade_id}"
            )

        if trade_record.result != "PENDING":
            raise ValueError(
                f"Trade {trade_record.trade_id} has already been settled "
                f"with result: {trade_record.result}"
            )

        is_call_direction: bool = trade_record.direction == "CALL"
        is_put_direction: bool = trade_record.direction == "PUT"

        trade_is_winning: bool = (
            (is_call_direction and exit_price > trade_record.entry_price)
            or (is_put_direction and exit_price < trade_record.entry_price)
        )

        if trade_is_winning:
            trade_result: str = "WIN"
            trade_profit_loss: float = trade_record.amount * self._payout_percentage
            self.current_balance += trade_record.amount + trade_profit_loss
        else:
            trade_result = "LOSS"
            trade_profit_loss = -trade_record.amount

        settled_trade_record = TradeRecord(
            trade_id=trade_record.trade_id,
            direction=trade_record.direction,
            entry_price=trade_record.entry_price,
            entry_time=trade_record.entry_time,
            exit_price=exit_price,
            exit_time=datetime.now(),
            duration_seconds=trade_record.duration_seconds,
            amount=trade_record.amount,
            result=trade_result,
            profit_loss=trade_profit_loss,
            agent_signals=trade_record.agent_signals,
            payout_percentage=trade_record.payout_percentage,
        )

        self._pending_trade = None
        self._trade_history.append(settled_trade_record)

        return settled_trade_record

    def has_pending_trade(self) -> bool:
        """Check whether a trade is currently pending settlement.

        Returns:
            True if there is a pending trade awaiting settlement,
            False otherwise.
        """
        return self._pending_trade is not None

    def get_pending_trade(self) -> Optional[TradeRecord]:
        """Retrieve the currently pending trade record, if any.

        Returns:
            The pending TradeRecord if one exists, or None if no
            trade is currently pending.
        """
        return self._pending_trade
