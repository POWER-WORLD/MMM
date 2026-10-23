"""
WebSocket Event Emitter Module for Gold Trading Analysis Platform.

This module provides a centralized event emitter for broadcasting
real-time updates to connected dashboard clients via Socket.IO.
It handles all WebSocket event types including price updates, candle
data, agent signals, trade notifications, and performance metrics.

Classes:
    DashboardEventEmitter: Centralized WebSocket event emitter for
        broadcasting real-time dashboard updates.
"""

import logging
from typing import Any, Dict, List

from flask_socketio import SocketIO

logger = logging.getLogger(__name__)


class DashboardEventEmitter:
    """Centralized WebSocket event emitter for real-time dashboard updates.

    Provides typed methods for emitting specific event types to all
    connected dashboard clients. Each method corresponds to a specific
    data update category and emits a named Socket.IO event with the
    appropriate payload structure.

    Supported Events:
        - price_update: Real-time gold price changes.
        - candle_update: New or updated candlestick data.
        - agent_signals: Analysis agent signal updates.
        - consensus_update: Aggregated consensus result.
        - trade_update: Trade placement and settlement notifications.
        - performance_update: Performance statistics refresh.
        - full_state: Complete state snapshot for new connections.

    Args:
        socket_io: The Flask-SocketIO instance used for emitting events
            to connected WebSocket clients.

    Example:
        >>> from flask_socketio import SocketIO
        >>> socket_io = SocketIO(app)
        >>> emitter = DashboardEventEmitter(socket_io)
        >>> emitter.emit_price_update(price=2650.50, timestamp="2024-01-01T12:00:00")
    """

    def __init__(self, socket_io: SocketIO) -> None:
        """Initialize the dashboard event emitter with a SocketIO instance.

        Args:
            socket_io: The Flask-SocketIO instance that will be used
                to broadcast events to all connected clients.
        """
        self._socket_io: SocketIO = socket_io

    def emit_price_update(self, price: float, timestamp: str) -> None:
        """Emit a real-time gold price update to all connected clients.

        Broadcasts the current gold price with its timestamp. Dashboard
        clients use this to update the live price display and add data
        points to the price chart.

        Args:
            price: The current gold price in USD per troy ounce.
            timestamp: ISO 8601 formatted timestamp of the price update.
        """
        price_data: Dict[str, Any] = {
            "price": price,
            "timestamp": timestamp,
        }

        try:
            self._socket_io.emit("price_update", price_data)
        except Exception as emission_error:
            logger.error(
                "Failed to emit price update: %s", str(emission_error)
            )

    def emit_candle_update(self, candle: Dict[str, Any]) -> None:
        """Emit a candlestick data update to all connected clients.

        Broadcasts new or updated candlestick data for the chart.
        Each candle typically contains open, high, low, close prices
        and a timestamp.

        Args:
            candle: Dictionary containing candlestick data with keys:
                - time (int/float): Unix timestamp of the candle.
                - open (float): Opening price.
                - high (float): Highest price during the period.
                - low (float): Lowest price during the period.
                - close (float): Closing price.
        """
        try:
            self._socket_io.emit("candle_update", candle)
        except Exception as emission_error:
            logger.error(
                "Failed to emit candle update: %s", str(emission_error)
            )

    def emit_agent_signals(self, signals: List[Dict[str, Any]]) -> None:
        """Emit analysis agent signal updates to all connected clients.

        Broadcasts the current signals from all analysis agents. Each
        signal includes the agent's name, recommended direction,
        confidence level, and reasoning.

        Args:
            signals: List of dictionaries, each representing an agent's
                signal with keys:
                - agent_name (str): Name of the analysis agent.
                - direction (str): Recommended direction ('CALL', 'PUT',
                    or 'NEUTRAL').
                - confidence (float): Confidence level (0.0 to 1.0).
                - reasoning (str): Brief explanation of the signal.
                - success_rate (float): Agent's historical success rate.
        """
        formatted_signals: List[Dict[str, Any]] = []
        for signal in signals:
            formatted_signal: Dict[str, Any] = {
                "agent_name": signal.get("agent_name", "Unknown Agent"),
                "direction": signal.get("direction", "NEUTRAL"),
                "confidence": signal.get("confidence", 0.0),
                "reasoning": signal.get("reasoning", ""),
                "success_rate": signal.get("success_rate", 0.0),
            }
            formatted_signals.append(formatted_signal)

        try:
            self._socket_io.emit("agent_signals", formatted_signals)
        except Exception as emission_error:
            logger.error(
                "Failed to emit agent signals: %s", str(emission_error)
            )

    def emit_consensus_result(self, consensus: Dict[str, Any]) -> None:
        """Emit the aggregated consensus result to all connected clients.

        Broadcasts the combined consensus from all analysis agents,
        including the agreed-upon direction and overall confidence.

        Args:
            consensus: Dictionary containing the consensus result with keys:
                - direction (str): Consensus direction ('CALL', 'PUT',
                    or 'NO_TRADE').
                - confidence (float): Overall confidence level.
                - agreeing_agents (int): Number of agents agreeing with
                    the consensus.
                - total_agents (int): Total number of agents.
                - reasoning (str): Summary of the consensus reasoning.
        """
        try:
            self._socket_io.emit("consensus_update", consensus)
        except Exception as emission_error:
            logger.error(
                "Failed to emit consensus result: %s", str(emission_error)
            )

    def emit_trade_update(self, trade: Dict[str, Any]) -> None:
        """Emit a trade status update to all connected clients.

        Broadcasts trade placement and settlement notifications.
        Used for both new trade placement and trade settlement events.

        Args:
            trade: Dictionary containing trade information with keys:
                - trade_id (str): Unique trade identifier.
                - direction (str): Trade direction ('CALL' or 'PUT').
                - entry_price (float): Price at trade entry.
                - exit_price (float or None): Price at settlement.
                - result (str): Trade result ('PENDING', 'WIN', 'LOSS').
                - profit_loss (float): Profit or loss amount in USD.
                - amount (float): Trade size in USD.
        """
        try:
            self._socket_io.emit("trade_update", trade)
        except Exception as emission_error:
            logger.error(
                "Failed to emit trade update: %s", str(emission_error)
            )

    def emit_performance_update(self, performance: Dict[str, Any]) -> None:
        """Emit updated performance statistics to all connected clients.

        Broadcasts refreshed performance metrics after each trade
        settlement. Dashboard clients use this to update the statistics
        display and performance charts.

        Args:
            performance: Dictionary containing performance statistics with
                keys matching PerformanceTracker.get_overall_statistics()
                output (total_trades, success_rate, total_profit_loss,
                current_balance, etc.).
        """
        try:
            self._socket_io.emit("performance_update", performance)
        except Exception as emission_error:
            logger.error(
                "Failed to emit performance update: %s", str(emission_error)
            )

    def emit_full_state(self, state: Dict[str, Any]) -> None:
        """Emit the complete platform state to all connected clients.

        Broadcasts a comprehensive state snapshot typically requested
        when a new client connects. Includes current price, all agent
        signals, active trade, and performance statistics.

        Args:
            state: Dictionary containing the complete platform state with
                optional keys:
                - current_price (float): Latest gold price.
                - candles (list): Recent candlestick data history.
                - agent_signals (list): Current signals from all agents.
                - consensus (dict): Current consensus result.
                - active_trade (dict or None): Currently active trade.
                - performance (dict): Current performance statistics.
                - recent_trades (list): Recent trade history.
        """
        try:
            self._socket_io.emit("full_state", state)
        except Exception as emission_error:
            logger.error(
                "Failed to emit full state: %s", str(emission_error)
            )
