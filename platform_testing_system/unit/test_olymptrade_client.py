"""
Unit Tests for Olymp Trade Integration Client Module.

Verifies simulated demo trading mode, credentials configuration, live demo
order dispatching, authorization headers, and error handling.
"""

from unittest.mock import MagicMock
import pytest

from platform_testing_system.synthetic_data.mock_network_data import (
    MockHttpResponse,
    MockNetworkDataFactory,
)
from trading.olymptrade_client import OlympTradeClient


class TestOlympTradeClient:
    """Test suite for OlympTradeClient."""

    def test_client_initialization_simulated_mode(self) -> None:
        """Verify client initializes in simulated demo mode by default."""
        client = OlympTradeClient(use_simulated_mode=True)
        assert client.is_simulated is True
        assert client.is_connected is False
        assert client.get_account_balance() == 10000.0

    def test_place_demo_trade_in_simulation_mode(self) -> None:
        """Verify placing a trade in simulation mode returns structured success dictionary."""
        client = OlympTradeClient(use_simulated_mode=True)
        order = client.place_demo_trade(
            asset_symbol="gold",
            direction="CALL",
            amount_usd=5.0,
            duration_seconds=60,
        )

        assert order["status"] == "success"
        assert order["direction"] == "CALL"
        assert order["amount"] == 5.0
        assert order["duration"] == 60
        assert order["asset"] == "gold"
        assert order["order_id"].startswith("sim_")

    def test_set_credentials_switches_to_live_mode(self) -> None:
        """Verify setting credentials enables connected status and updates session headers."""
        client = OlympTradeClient(use_simulated_mode=True)
        ok = client.set_credentials(auth_token="test_bearer_token_abc", account_id="demo_acc_123")

        assert ok is True
        assert client.is_connected is True
        assert client.is_simulated is False
        assert client._session.headers.get("Authorization") == "Bearer test_bearer_token_abc"

    def test_live_order_dispatch_success(self) -> None:
        """Verify client dispatches HTTP POST when in live demo mode."""
        client = OlympTradeClient(auth_token="dummy_token", use_simulated_mode=False)

        mock_payload = MockNetworkDataFactory.create_olymp_trade_order_payload(
            order_id="ot_live_12345",
            direction="PUT",
            amount=1.0,
        )
        session_mock = MagicMock()
        session_mock.post.return_value = MockHttpResponse(json_data=mock_payload, status_code=200)
        client._session = session_mock

        order = client.place_demo_trade(
            asset_symbol="gold",
            direction="PUT",
            amount_usd=1.0,
            duration_seconds=60,
        )

        assert order["status"] == "success"
        assert order["order_id"] == "ot_live_12345"
        session_mock.post.assert_called_once()

    def test_live_order_dispatch_api_error_handling(self) -> None:
        """Verify client handles API errors gracefully and returns error dictionary."""
        client = OlympTradeClient(auth_token="dummy_token", use_simulated_mode=False)

        error_payload = MockNetworkDataFactory.create_olymp_trade_error_payload("Insufficient balance")
        session_mock = MagicMock()
        session_mock.post.return_value = MockHttpResponse(json_data=error_payload, status_code=400)
        client._session = session_mock

        order = client.place_demo_trade(
            asset_symbol="gold",
            direction="CALL",
            amount_usd=100.0,
            duration_seconds=60,
        )

        assert order["status"] == "error"
        assert "Insufficient balance" in order["message"]
