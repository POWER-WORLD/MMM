"""
End-to-End Platform Orchestrator Integration Tests.

Verifies the master GoldTradingPlatform orchestrator lifecycle, synthetic candle loading,
synchronous multi-agent analysis cycles, trade placement, settlement, and shutdown.
"""

from datetime import datetime, timezone
import pytest

from agents.base_agent import TradeDirection
from main import GoldTradingPlatform
from platform_testing_system.synthetic_data.market_regimes import (
    MarketRegimeGenerator,
    MarketRegimeType,
)


class TestFullPlatformE2E:
    """End-to-end integration tests for GoldTradingPlatform."""

    def test_platform_initialization_and_runtime_config(self) -> None:
        """Verify GoldTradingPlatform initializes all components and manages runtime configuration."""
        platform = GoldTradingPlatform()

        # Check default runtime config
        cfg = platform._get_runtime_config()
        assert cfg["candle_interval_seconds"] == 10
        assert cfg["trade_duration_seconds"] == 60
        assert cfg["trade_amount_usd"] == 1.0

        # Update runtime config
        updates = {
            "candle_interval_seconds": 30,
            "trade_duration_seconds": 120,
            "trade_amount_usd": 5.0,
        }
        updated_cfg = platform._update_runtime_config(updates)
        assert updated_cfg["candle_interval_seconds"] == 30
        assert updated_cfg["trade_duration_seconds"] == 120
        assert updated_cfg["trade_amount_usd"] == 5.0
        assert platform.active_candle_interval_seconds == 30
        assert platform.active_trade_duration_seconds == 120
        assert platform.active_trade_amount_usd == 5.0

    def test_platform_synthetic_data_loading_and_analysis_cycle(self) -> None:
        """Verify platform loads synthetic candles and executes a full analysis cycle."""
        platform = GoldTradingPlatform()

        # Load 80 synthetic candles
        candles_df = MarketRegimeGenerator.generate_regime(MarketRegimeType.BULL_TREND, count=80)
        platform.load_candles_dataframe(candles_df)

        assert platform.data_store.get_candle_count() == 80
        latest_price = platform.data_store.get_latest_price()
        assert latest_price is not None

        # Execute analysis cycle synchronously
        platform.run_analysis_cycle()

        state = platform._get_full_state_dict()
        assert state["current_price"] == latest_price
        assert len(state["candles"]) == 80
        assert len(state["agent_signals"]) == 7
        assert state["consensus"] is not None
        assert state["performance"] is not None

    def test_platform_trade_placement_and_settlement(self) -> None:
        """Verify platform handles trade placement, pending trade query, and settlement."""
        platform = GoldTradingPlatform()

        # Load data to set current price
        candles_df = MarketRegimeGenerator.generate_regime(MarketRegimeType.BULL_TREND, count=50)
        platform.load_candles_dataframe(candles_df)
        entry_price = platform.data_store.get_latest_price()

        # Place trade
        platform._attempt_trade_placement(
            direction=TradeDirection.CALL,
            signals=[],
            average_confidence=0.85,
        )

        assert platform.trade_executor.has_pending_trade() is True
        active_info = platform._get_active_trade_info()
        assert active_info is not None
        assert active_info["direction"] == "CALL"
        assert active_info["entry_price"] == entry_price

        # Settle active trade immediately as WIN (exit = entry + 5.0)
        settled_info = platform.settle_active_trade(exit_price=entry_price + 5.0)
        assert settled_info is not None
        assert settled_info["result"] == "WIN"
        assert settled_info["profit_loss"] > 0
        assert platform.trade_executor.has_pending_trade() is False

        # Verify performance updated
        perf = platform.performance_tracker.get_overall_statistics()
        assert perf["total_trades"] == 1
        assert perf["winning_trades"] == 1

        # Stop platform
        platform.stop()
        assert platform._is_running is False
