"""
Integration Tests for Dashboard State Synchronization Pipeline.

Verifies that in-memory changes across PlatformDataStore, TradeExecutor,
and PerformanceTracker immediately reflect across dashboard REST endpoints.
"""

from datetime import datetime, timezone
import pytest

from core.data_store import PlatformDataStore
from dashboard.app import create_dashboard_application
from platform_testing_system.synthetic_data.market_regimes import (
    MarketRegimeGenerator,
    MarketRegimeType,
)
from trading.performance_tracker import PerformanceTracker
from trading.trade_executor import TradeRecord


class TestDashboardIntegration:
    """Pipeline integration test: DataStore & Tracker -> Flask Dashboard REST Endpoints."""

    @pytest.fixture
    def dashboard_pipeline(self):
        """Instantiate data store, performance tracker, and dashboard test client."""
        data_store = PlatformDataStore(max_candles=100)
        tracker = PerformanceTracker(initial_balance=10000.0)

        runtime_config = {
            "candle_interval_seconds": 10,
            "trade_duration_seconds": 60,
            "trade_amount_usd": 1.0,
            "payout_percentage": 0.82,
        }

        def get_full_state():
            price, ts = data_store.get_current_price()
            candles_df = data_store.get_candles_dataframe()
            candles_list = []
            if not candles_df.empty:
                for _, row in candles_df.iterrows():
                    candles_list.append({
                        "time": 1700000000,
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                    })

            return {
                "current_price": price,
                "price_timestamp": ts.isoformat() if ts else None,
                "candles": candles_list,
                "agent_signals": data_store.get_agent_signals(),
                "consensus": {},
                "performance": tracker.get_overall_statistics(),
                "recent_trades": tracker.get_recent_trades(),
                "active_trade": None,
                "current_balance": 10000.0,
            }

        def update_config(updates):
            runtime_config.update(updates)
            return runtime_config

        app, socket_io = create_dashboard_application(
            get_state_callback=get_full_state,
            get_config_callback=lambda: runtime_config,
            update_config_callback=update_config,
        )
        app.config["TESTING"] = True
        return data_store, tracker, app.test_client()

    def test_live_price_and_candles_reflection_in_rest_api(self, dashboard_pipeline) -> None:
        """Verify adding candles to data_store updates /api/price and /api/candles."""
        data_store, _, client = dashboard_pipeline

        # Populate data store with synthetic regime
        candles_df = MarketRegimeGenerator.generate_regime(MarketRegimeType.BULL_TREND, count=40)
        for _, row in candles_df.iterrows():
            data_store.add_candle(dict(row))

        latest_close = float(candles_df.iloc[-1]["close"])
        data_store.set_current_price(latest_close, datetime.now(tz=timezone.utc))

        # Query /api/price
        res_price = client.get("/api/price")
        assert res_price.status_code == 200
        assert res_price.get_json()["price"] == latest_close

        # Query /api/candles
        res_candles = client.get("/api/candles")
        assert res_candles.status_code == 200
        assert len(res_candles.get_json()) == 40

    def test_trade_settlement_reflection_in_performance_endpoint(self, dashboard_pipeline) -> None:
        """Verify recording a settled trade reflects in /api/performance and /api/trades."""
        _, tracker, client = dashboard_pipeline

        rec = TradeRecord(
            trade_id="dash_test_t1",
            direction="CALL",
            entry_price=4100.0,
            entry_time=datetime.now(tz=timezone.utc),
            exit_price=4104.0,
            exit_time=datetime.now(tz=timezone.utc),
            duration_seconds=60,
            amount=10.0,
            result="WIN",
            profit_loss=8.20,
        )
        tracker.record_trade(rec)

        # Query /api/performance
        res_perf = client.get("/api/performance")
        assert res_perf.status_code == 200
        perf_data = res_perf.get_json()
        assert perf_data["total_trades"] == 1
        assert perf_data["winning_trades"] == 1
        assert perf_data["total_profit_loss"] == 8.20

        # Query /api/trades
        res_trades = client.get("/api/trades")
        assert res_trades.status_code == 200
        trades_data = res_trades.get_json()
        assert len(trades_data["recent_trades"]) == 1
        assert trades_data["recent_trades"][0]["trade_id"] == "dash_test_t1"
