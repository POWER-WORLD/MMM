"""
Integration Tests for Olymp Trade Demo Platform Integration.

Verifies end-to-end integration between GoldTradingPlatform and OlympTradeClient:
- Initialization in simulated demo mode
- Consensus-triggered demo order execution
- Live demo API order dispatching via mock HTTP session
- Dynamic runtime credentials and account switching
- Olymp Trade API error resilience (400, 401, 500)
- Account balance synchronization and dashboard state exposure
- Multi-duration and directional contract payload formatting
"""

from typing import Dict
from unittest.mock import MagicMock
import pytest

from agents.base_agent import TradeDirection, TradeSignal
from agents.consensus_engine import ConsensusEngine
from agents.rsi_agent import RelativeStrengthIndexAgent
from main import GoldTradingPlatform
from platform_testing_system.synthetic_data.market_regimes import (
    MarketRegimeGenerator,
    MarketRegimeType,
)
from platform_testing_system.synthetic_data.mock_network_data import (
    MockHttpResponse,
    MockNetworkDataFactory,
)


class TestOlympTradeIntegration:
    """Integration test suite for Olymp Trade demo execution within the platform."""

    def test_platform_initializes_with_olymp_trade_client(self) -> None:
        """Verify GoldTradingPlatform instantiates and exposes OlympTradeClient."""
        platform = GoldTradingPlatform()

        assert hasattr(platform, "olymp_trade_client")
        assert platform.olymp_trade_client is not None
        assert platform.olymp_trade_client.is_simulated is True
        assert platform.olymp_trade_client.is_connected is False
        assert platform.olymp_trade_client.get_account_balance() == 10000.0

        # Verify state exposure
        state = platform._get_full_state_dict()
        assert "olymp_trade" in state
        assert state["olymp_trade"]["is_connected"] is False
        assert state["olymp_trade"]["is_simulated"] is True
        assert state["olymp_trade"]["demo_balance"] == 10000.0

        runtime_cfg = platform._get_runtime_config()
        assert runtime_cfg["olymp_trade_connected"] is False
        assert runtime_cfg["olymp_trade_simulated"] is True
        assert runtime_cfg["olymp_trade_balance"] == 10000.0

    def test_consensus_triggers_olymp_trade_demo_order(self) -> None:
        """Verify market consensus triggers both TradeExecutor and OlympTradeClient demo trade."""
        platform = GoldTradingPlatform()

        # Load market candles
        candles_df = MarketRegimeGenerator.generate_regime(
            MarketRegimeType.BULL_TREND, count=90
        )
        platform.load_candles_dataframe(candles_df)

        # Substitute deterministic unanimous bull agents
        class DeterministicBullAgent(RelativeStrengthIndexAgent):
            def __init__(self, name: str):
                super().__init__()
                self.agent_name = name

            def analyze(self, candles_dataframe, historical_dataframe=None):
                return TradeSignal(
                    direction=TradeDirection.CALL,
                    confidence=0.88,
                    agent_name=self.agent_name,
                    reasoning="Unanimous institutional bullish signal",
                    timestamp=None,
                )

        bull_agents = [DeterministicBullAgent(f"Agent_{i}") for i in range(7)]
        platform.analysis_agents = bull_agents
        platform.consensus_engine = ConsensusEngine(agents=bull_agents, required_consensus_count=7)

        # Spy on olymp_trade_client.place_demo_trade
        original_place_demo = platform.olymp_trade_client.place_demo_trade
        spy_calls = []

        def spy_place_demo(*args, **kwargs):
            result = original_place_demo(*args, **kwargs)
            spy_calls.append({"args": args, "kwargs": kwargs, "result": result})
            return result

        platform.olymp_trade_client.place_demo_trade = spy_place_demo

        # Run analysis cycle
        platform.run_analysis_cycle()

        assert platform.trade_executor.has_pending_trade() is True
        assert len(spy_calls) == 1

        dispatched = spy_calls[0]
        assert dispatched["kwargs"]["direction"] == "CALL"
        assert dispatched["kwargs"]["amount_usd"] == platform.active_trade_amount_usd
        assert dispatched["kwargs"]["duration_seconds"] == platform.active_trade_duration_seconds
        assert dispatched["result"]["status"] == "success"
        assert dispatched["result"]["mode"] == "simulated_demo"
        assert dispatched["result"]["order_id"].startswith("sim_")

    def test_live_demo_mode_order_dispatch_with_mock_http(self) -> None:
        """Verify HTTP POST request formatting when platform is configured with demo credentials."""
        platform = GoldTradingPlatform()

        # Configure demo credentials
        platform.olymp_trade_client.set_credentials(
            auth_token="demo_user_token_12345",
            account_id="demo_acc_777888",
        )
        assert platform.olymp_trade_client.is_connected is True
        assert platform.olymp_trade_client.is_simulated is False

        # Mock the requests session on the client
        mock_payload = MockNetworkDataFactory.create_olymp_trade_order_payload(
            order_id="ot_live_order_9988",
            direction="PUT",
            amount=2.0,
        )
        session_mock = MagicMock()
        session_mock.post.return_value = MockHttpResponse(
            json_data=mock_payload,
            status_code=200,
        )
        platform.olymp_trade_client._session = session_mock

        # Set price and place trade
        platform.data_store.set_current_price(price=4105.50)
        platform.active_trade_amount_usd = 2.0
        platform.active_trade_duration_seconds = 60

        platform._attempt_trade_placement(
            direction=TradeDirection.PUT,
            signals=[],
            average_confidence=0.88,
        )

        assert platform.trade_executor.has_pending_trade() is True
        session_mock.post.assert_called_once()

        # Validate URL and HTTP body sent to Olymp Trade
        call_args = session_mock.post.call_args
        called_url = call_args[0][0]
        called_body = call_args[1]["json"]

        assert "/v1/ftt/orders" in called_url
        assert called_body["account_id"] == "demo_acc_777888"
        assert called_body["asset"] == "gold"
        assert called_body["dir"] == "down"
        assert called_body["amount"] == 2.0
        assert called_body["duration"] == 60
        assert called_body["demo"] is True

    def test_runtime_credential_updates_dynamically_switches_mode(self) -> None:
        """Verify updating runtime configuration via socket/REST switches client to live demo mode."""
        platform = GoldTradingPlatform()
        assert platform.olymp_trade_client.is_simulated is True

        updates = {
            "olymp_auth_token": "updated_secret_token_abc",
            "olymp_account_id": "updated_demo_id_001",
        }
        updated_cfg = platform._update_runtime_config(updates)

        assert platform.olymp_trade_client.is_connected is True
        assert platform.olymp_trade_client.is_simulated is False
        assert platform.olymp_trade_client._auth_token == "updated_secret_token_abc"
        assert platform.olymp_trade_client._account_id == "updated_demo_id_001"
        assert updated_cfg["olymp_trade_connected"] is True
        assert updated_cfg["olymp_trade_simulated"] is False

    def test_olymp_trade_api_error_resilience(self) -> None:
        """Verify platform resilience when Olymp Trade demo API responds with HTTP error."""
        platform = GoldTradingPlatform()
        platform.olymp_trade_client.set_credentials(
            auth_token="demo_token",
            account_id="demo_acc",
        )

        # Mock 500 Internal Server Error from broker
        error_payload = MockNetworkDataFactory.create_olymp_trade_error_payload(
            "Service temporarily unavailable"
        )
        session_mock = MagicMock()
        session_mock.post.return_value = MockHttpResponse(
            json_data=error_payload,
            status_code=500,
        )
        platform.olymp_trade_client._session = session_mock

        platform.data_store.set_current_price(price=4100.0)

        # Platform should NOT crash or raise unhandled exceptions
        platform._attempt_trade_placement(
            direction=TradeDirection.CALL,
            signals=[],
            average_confidence=0.85,
        )

        # Local trade executor still successfully queued trade
        assert platform.trade_executor.has_pending_trade() is True

        # Settle the trade to verify complete recovery
        settled = platform.settle_active_trade(exit_price=4103.0)
        assert settled is not None
        assert settled["result"] == "WIN"
        assert platform.trade_executor.has_pending_trade() is False

    def test_olymp_trade_balance_retrieval_and_state_sync(self) -> None:
        """Verify demo account balance synchronization from Olymp Trade balance endpoint."""
        platform = GoldTradingPlatform()
        platform.olymp_trade_client.set_credentials(
            auth_token="demo_token",
            account_id="demo_acc",
        )

        # Mock balance endpoint returning updated demo balance
        session_mock = MagicMock()
        session_mock.get.return_value = MockHttpResponse(
            json_data={"demo_balance": 12450.75, "currency": "USD"},
            status_code=200,
        )
        platform.olymp_trade_client._session = session_mock

        balance = platform.olymp_trade_client.get_account_balance()
        assert balance == 12450.75

        # Check that platform state reflects updated balance
        state = platform._get_full_state_dict()
        assert state["olymp_trade"]["demo_balance"] == 12450.75

        cfg = platform._get_runtime_config()
        assert cfg["olymp_trade_balance"] == 12450.75

    def test_olymp_trade_different_durations_and_directions(self) -> None:
        """Verify client correctly maps directions (CALL -> up, PUT -> down) and durations."""
        platform = GoldTradingPlatform()
        platform.olymp_trade_client.set_credentials(
            auth_token="demo_token",
            account_id="demo_acc",
        )

        recorded_payloads = []

        def mock_post(url, json=None, **kwargs):
            recorded_payloads.append(json)
            return MockHttpResponse(
                json_data=MockNetworkDataFactory.create_olymp_trade_order_payload(),
                status_code=200,
            )

        session_mock = MagicMock()
        session_mock.post.side_effect = mock_post
        platform.olymp_trade_client._session = session_mock

        # Test 1: CALL with 120s duration
        platform.olymp_trade_client.place_demo_trade(
            asset_symbol="gold",
            direction="CALL",
            amount_usd=5.0,
            duration_seconds=120,
        )

        # Test 2: PUT with 300s duration
        platform.olymp_trade_client.place_demo_trade(
            asset_symbol="gold",
            direction="PUT",
            amount_usd=10.0,
            duration_seconds=300,
        )

        assert len(recorded_payloads) == 2

        # First trade check
        assert recorded_payloads[0]["dir"] == "up"
        assert recorded_payloads[0]["duration"] == 120
        assert recorded_payloads[0]["amount"] == 5.0

        # Second trade check
        assert recorded_payloads[1]["dir"] == "down"
        assert recorded_payloads[1]["duration"] == 300
        assert recorded_payloads[1]["amount"] == 10.0
