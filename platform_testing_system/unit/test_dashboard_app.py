"""
Unit Tests for Flask Dashboard Application and REST API Endpoints.

Verifies route handlers, status codes, payload schemas, CORS headers,
configuration retrieval/update, and state query endpoints using Flask's test client.
"""

import json
from datetime import datetime, timezone
import pytest

from dashboard.app import create_dashboard_application


class TestDashboardApplication:
    """Test suite for Flask dashboard application and REST endpoints."""

    @pytest.fixture
    def test_app_and_client(self):
        """Create a configured Flask application and test client."""
        mock_state = {
            "current_price": 4102.50,
            "price_timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "candles": [{"time": 1700000000, "open": 4100.0, "high": 4105.0, "low": 4095.0, "close": 4102.5}],
            "agent_signals": [{"agent_name": "RSI", "direction": "CALL", "confidence": 0.8}],
            "consensus": {"consensus_reached": True, "direction": "CALL"},
            "agent_statistics": [{"agent_name": "RSI", "success_rate": 75.0}],
            "performance": {"total_trades": 10, "winning_trades": 8, "losing_trades": 2, "success_rate": 80.0},
            "recent_trades": [{"trade_id": "t1", "result": "WIN"}],
            "active_trade": {"trade_id": "active_001", "entry_price": 4100.0},
        }

        runtime_config = {
            "candle_interval_seconds": 10,
            "trade_duration_seconds": 60,
            "trade_amount_usd": 2.50,
        }

        def mock_update_config(updates):
            runtime_config.update(updates)
            return runtime_config

        app, socket_io = create_dashboard_application(
            get_state_callback=lambda: mock_state,
            get_config_callback=lambda: runtime_config,
            update_config_callback=mock_update_config,
        )
        app.config["TESTING"] = True
        return app.test_client(), mock_state, runtime_config

    def test_api_status_endpoint(self, test_app_and_client) -> None:
        """Verify GET /api/status returns operational metadata and CORS headers."""
        client, _, _ = test_app_and_client
        res = client.get("/api/status")
        assert res.status_code == 200
        assert res.headers.get("Access-Control-Allow-Origin") == "*"

        data = res.get_json()
        assert data["status"] == "running"
        assert data["websocket_active"] is True
        assert "server_time" in data

    def test_api_state_endpoint(self, test_app_and_client) -> None:
        """Verify GET /api/state returns full platform snapshot."""
        client, mock_state, _ = test_app_and_client
        res = client.get("/api/state")
        assert res.status_code == 200
        data = res.get_json()
        assert data["current_price"] == 4102.50
        assert len(data["candles"]) == 1
        assert data["consensus"]["direction"] == "CALL"

    def test_api_price_endpoint(self, test_app_and_client) -> None:
        """Verify GET /api/price returns current price and timestamp."""
        client, _, _ = test_app_and_client
        res = client.get("/api/price")
        assert res.status_code == 200
        data = res.get_json()
        assert data["price"] == 4102.50
        assert data["timestamp"] is not None

    def test_api_candles_endpoint(self, test_app_and_client) -> None:
        """Verify GET /api/candles returns candle buffer list."""
        client, _, _ = test_app_and_client
        res = client.get("/api/candles")
        assert res.status_code == 200
        data = res.get_json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["close"] == 4102.5

    def test_api_signals_endpoint(self, test_app_and_client) -> None:
        """Verify GET /api/signals returns agent signals and consensus."""
        client, _, _ = test_app_and_client
        res = client.get("/api/signals")
        assert res.status_code == 200
        data = res.get_json()
        assert len(data["agent_signals"]) == 1
        assert data["consensus"]["consensus_reached"] is True

    def test_api_performance_endpoint(self, test_app_and_client) -> None:
        """Verify GET /api/performance returns statistics."""
        client, _, _ = test_app_and_client
        res = client.get("/api/performance")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success_rate"] == 80.0
        assert data["total_trades"] == 10

    def test_api_trades_endpoint(self, test_app_and_client) -> None:
        """Verify GET /api/trades returns active trade and history."""
        client, _, _ = test_app_and_client
        res = client.get("/api/trades")
        assert res.status_code == 200
        data = res.get_json()
        assert data["active_trade"]["trade_id"] == "active_001"
        assert len(data["recent_trades"]) == 1

    def test_api_config_get_and_post(self, test_app_and_client) -> None:
        """Verify GET /api/config and POST /api/config for runtime parameter updates."""
        client, _, _ = test_app_and_client

        # 1. GET
        res_get = client.get("/api/config")
        assert res_get.status_code == 200
        assert res_get.get_json()["trade_amount_usd"] == 2.50

        # 2. POST update
        updates = {"trade_amount_usd": 5.0, "trade_duration_seconds": 120}
        res_post = client.post(
            "/api/config",
            data=json.dumps(updates),
            content_type="application/json",
        )
        assert res_post.status_code == 200
        data_post = res_post.get_json()
        assert data_post["status"] == "success"
        assert data_post["config"]["trade_amount_usd"] == 5.0
        assert data_post["config"]["trade_duration_seconds"] == 120
