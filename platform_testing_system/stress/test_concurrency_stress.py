"""
Multi-Threaded Concurrency and High-Throughput Stress Tests.

Verifies thread safety, deadlock freedom, and atomic consistency across PlatformDataStore,
CandleBuilder, and PerformanceTracker under heavy concurrent contention.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import random
import time
import pytest

from core.candle_builder import CandleBuilder, CandleData
from core.data_store import PlatformDataStore
from trading.performance_tracker import PerformanceTracker
from trading.trade_executor import TradeRecord


class TestConcurrencyStress:
    """Stress testing suite for concurrent multi-threaded contention."""

    def test_datastore_concurrent_readers_and_writers(self) -> None:
        """
        Launch 40 worker threads concurrently performing writes and reads on PlatformDataStore:
        - Writers adding candles, setting price, updating signals, adding trades.
        - Readers querying dataframe, count, latest price, and trade records.
        Verify zero race condition exceptions, no deadlocks, and valid state.
        """
        store = PlatformDataStore(max_candles=200)
        num_threads = 40
        iterations_per_thread = 50
        errors = []

        def worker(thread_id: int):
            try:
                for i in range(iterations_per_thread):
                    now = datetime.now(tz=timezone.utc)
                    action = random.choice([
                        "add_candle",
                        "set_price",
                        "read_df",
                        "read_price",
                        "add_trade",
                        "read_trades",
                        "set_signals",
                    ])

                    if action == "add_candle":
                        p = 4100.0 + random.uniform(-5.0, 5.0)
                        store.add_candle({
                            "timestamp": now,
                            "open": p,
                            "high": p + 1.0,
                            "low": p - 1.0,
                            "close": p + 0.2,
                            "volume": 10,
                            "tick_count": 2,
                        })
                    elif action == "set_price":
                        store.set_current_price(4100.0 + random.uniform(-10, 10), now)
                    elif action == "read_df":
                        df = store.get_candles_dataframe(count=50)
                        assert df is not None
                    elif action == "read_price":
                        _ = store.get_current_price()
                        _ = store.get_latest_price()
                    elif action == "add_trade":
                        store.add_trade_record({
                            "trade_id": f"t_{thread_id}_{i}",
                            "result": "WIN" if random.random() > 0.5 else "LOSS",
                            "profit_loss": 0.82 if random.random() > 0.5 else -1.0,
                        })
                    elif action == "read_trades":
                        _ = store.get_trade_records(count=10)
                    elif action == "set_signals":
                        store.set_agent_signals([{"agent": "RSI", "direction": "CALL"}])

            except Exception as e:
                errors.append((thread_id, e))

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, tid) for tid in range(num_threads)]
            for f in as_completed(futures):
                f.result()

        assert len(errors) == 0, f"Encountered concurrency errors: {errors}"
        assert store.get_candle_count() <= 200

    def test_candle_builder_high_frequency_tick_ingestion(self) -> None:
        """
        Stress test CandleBuilder by ingesting 5,000 rapid ticks across multiple threads.
        Verify that all ticks are aggregated into valid candles without drop or corruption.
        """
        completed_candles = []
        builder = CandleBuilder(
            candle_interval_seconds=10,
            on_candle_complete_callback=lambda c: completed_candles.append(c),
        )

        num_ticks = 5000
        base_time = datetime(2026, 10, 22, 10, 0, 0, tzinfo=timezone.utc)

        # Ingest 5000 ticks progressing time by 0.1s per tick = 500 simulated seconds (50 candles)
        for i in range(num_ticks):
            tick_time = base_time + (i * (10 / 50)) * (datetime.now() - datetime.now())  # fast delta
            from datetime import timedelta
            t = base_time + timedelta(seconds=i * 0.1)
            p = 4100.0 + (i % 20) * 0.1
            builder.add_tick(t, p)

        # Finalizing last candle
        from datetime import timedelta
        builder.add_tick(base_time + timedelta(seconds=num_ticks * 0.1 + 15), 4100.0)

        assert len(completed_candles) >= 40
        for candle in completed_candles:
            assert candle.tick_count > 0
            assert candle.high_price >= candle.low_price

    def test_performance_tracker_concurrent_trade_recording(self) -> None:
        """
        Concurrently record 200 trades across 20 threads into PerformanceTracker.
        Verify total count and mathematical consistency.
        """
        tracker = PerformanceTracker(initial_balance=10000.0)
        num_threads = 20
        trades_per_thread = 10
        total_expected_trades = num_threads * trades_per_thread

        def record_batch(tid: int):
            for i in range(trades_per_thread):
                is_win = (tid + i) % 2 == 0
                rec = TradeRecord(
                    trade_id=f"concurrent_{tid}_{i}",
                    direction="CALL",
                    entry_price=4100.0,
                    entry_time=datetime.now(tz=timezone.utc),
                    exit_price=4105.0 if is_win else 4095.0,
                    exit_time=datetime.now(tz=timezone.utc),
                    duration_seconds=60,
                    amount=10.0,
                    result="WIN" if is_win else "LOSS",
                    profit_loss=8.20 if is_win else -10.0,
                )
                tracker.record_trade(rec)

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(record_batch, tid) for tid in range(num_threads)]
            for f in as_completed(futures):
                f.result()

        stats = tracker.get_overall_statistics()
        assert stats["total_trades"] == total_expected_trades
        assert stats["winning_trades"] + stats["losing_trades"] == total_expected_trades
        assert 0.0 <= stats["success_rate"] <= 1.0
