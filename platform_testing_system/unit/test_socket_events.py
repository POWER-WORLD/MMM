"""
Unit Tests for Dashboard WebSocket Event Emitter Module.

Verifies event emission formatting, payload schemas, Socket.IO call arguments,
and graceful handling of broken connections or emission exceptions.
"""

from unittest.mock import MagicMock
import pytest

from dashboard.socket_events import DashboardEventEmitter


class TestDashboardEventEmitter:
    """Test suite for DashboardEventEmitter."""

    @pytest.fixture
    def mock_socket_io(self):
        """Create a mock SocketIO instance."""
        return MagicMock()

    def test_emit_price_update(self, mock_socket_io) -> None:
        """Verify emit_price_update emits price_update event with price and timestamp."""
        emitter = DashboardEventEmitter(mock_socket_io)
        emitter.emit_price_update(price=4100.50, timestamp="2026-10-22T14:30:00Z")

        mock_socket_io.emit.assert_called_once_with(
            "price_update",
            {"price": 4100.50, "timestamp": "2026-10-22T14:30:00Z"},
        )

    def test_emit_candle_update(self, mock_socket_io) -> None:
        """Verify emit_candle_update emits candle_update event with candle payload."""
        emitter = DashboardEventEmitter(mock_socket_io)
        candle = {"time": 1700000000, "open": 4100.0, "high": 4105.0, "low": 4095.0, "close": 4102.0}
        emitter.emit_candle_update(candle)

        mock_socket_io.emit.assert_called_once_with("candle_update", candle)

    def test_emit_agent_signals(self, mock_socket_io) -> None:
        """Verify emit_agent_signals standardizes and broadcasts agent signals."""
        emitter = DashboardEventEmitter(mock_socket_io)
        signals = [
            {"agent_name": "RSI", "direction": "CALL", "confidence": 0.85, "reasoning": "Oversold"},
        ]
        emitter.emit_agent_signals(signals)

        mock_socket_io.emit.assert_called_once()
        args, _ = mock_socket_io.emit.call_args
        assert args[0] == "agent_signals"
        assert len(args[1]) == 1
        assert args[1][0]["agent_name"] == "RSI"
        assert args[1][0]["direction"] == "CALL"

    def test_emit_consensus_result(self, mock_socket_io) -> None:
        """Verify emit_consensus_result emits consensus_update."""
        emitter = DashboardEventEmitter(mock_socket_io)
        consensus = {"consensus_reached": True, "direction": "CALL", "agreeing_agents": 7}
        emitter.emit_consensus_result(consensus)

        mock_socket_io.emit.assert_called_once_with("consensus_update", consensus)

    def test_emit_trade_update(self, mock_socket_io) -> None:
        """Verify emit_trade_update emits trade_update."""
        emitter = DashboardEventEmitter(mock_socket_io)
        trade = {"trade_id": "t1", "result": "WIN", "profit_loss": 0.82}
        emitter.emit_trade_update(trade)

        mock_socket_io.emit.assert_called_once_with("trade_update", trade)

    def test_emit_performance_update(self, mock_socket_io) -> None:
        """Verify emit_performance_update emits performance_update."""
        emitter = DashboardEventEmitter(mock_socket_io)
        perf = {"total_trades": 5, "success_rate": 80.0}
        emitter.emit_performance_update(perf)

        mock_socket_io.emit.assert_called_once_with("performance_update", perf)

    def test_emit_full_state(self, mock_socket_io) -> None:
        """Verify emit_full_state emits full_state."""
        emitter = DashboardEventEmitter(mock_socket_io)
        state = {"current_price": 4100.0, "candles": []}
        emitter.emit_full_state(state)

        mock_socket_io.emit.assert_called_once_with("full_state", state)

    def test_emission_exception_handled_gracefully(self, mock_socket_io) -> None:
        """Verify exception during socket emit does not propagate or crash the application."""
        mock_socket_io.emit.side_effect = RuntimeError("Broken pipe on websocket")
        emitter = DashboardEventEmitter(mock_socket_io)

        # Must not raise an exception
        emitter.emit_price_update(4100.0, "2026-10-22T14:30:00Z")
        emitter.emit_candle_update({})
        emitter.emit_agent_signals([])
        emitter.emit_consensus_result({})
        emitter.emit_trade_update({})
        emitter.emit_performance_update({})
        emitter.emit_full_state({})
