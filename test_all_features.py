"""
Comprehensive Verification Test Suite for Gold Trading Analysis Platform.

Tests all platform features one by one:
1. Real-time Gold Price Engine
2. 10-Second Candle Builder
3. 7 Specialized Technical Analysis Agents
4. Consensus Engine (7/7 Unanimous Requirement)
5. 1-Minute Trade Execution & 60-Second Settlement Engine
6. Performance & Win Rate Tracker
7. REST API Endpoints
8. Olymp Trade Integration Client
"""

import sys
import time
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np

from config import PLATFORM_CONFIG
from core.price_engine import GoldPriceEngine
from core.candle_builder import CandleBuilder, CandleData
from core.data_store import PlatformDataStore
from agents.base_agent import TradeDirection, TradeSignal
from agents.rsi_agent import RelativeStrengthIndexAgent
from agents.macd_agent import MovingAverageConvergenceDivergenceAgent
from agents.bollinger_agent import BollingerBandsAgent
from agents.ema_crossover_agent import ExponentialMovingAverageCrossoverAgent
from agents.stochastic_agent import StochasticOscillatorAgent
from agents.adx_agent import AverageDirectionalIndexAgent
from agents.ichimoku_agent import IchimokuCloudAgent
from agents.consensus_engine import ConsensusEngine
from trading.trade_executor import TradeExecutor
from trading.performance_tracker import PerformanceTracker
from trading.olymptrade_client import OlympTradeClient


def generate_synthetic_candles(count: int = 100, base_price: float = 4100.0) -> pd.DataFrame:
    """Helper to generate realistic synthetic OHLCV candles for testing."""
    np.random.seed(42)
    now = datetime.now(tz=timezone.utc)
    timestamps = [now - timedelta(seconds=10 * (count - i)) for i in range(count)]
    
    prices = [base_price]
    for _ in range(count - 1):
        change = np.random.normal(0, 0.4)
        prices.append(prices[-1] + change)
        
    candles = []
    for i in range(count):
        p = prices[i]
        high = p + abs(np.random.normal(0, 0.3))
        low = p - abs(np.random.normal(0, 0.3))
        open_p = low + (high - low) * np.random.uniform(0.2, 0.8)
        close_p = low + (high - low) * np.random.uniform(0.2, 0.8)
        candles.append({
            "timestamp": timestamps[i],
            "open": open_p,
            "high": high,
            "low": low,
            "close": close_p,
            "volume": int(np.random.uniform(10, 100)),
        })
    return pd.DataFrame(candles)


def test_feature_1_price_engine() -> bool:
    print("\n" + "=" * 60)
    print("TEST 1: Real-Time Gold Price Engine")
    print("=" * 60)
    
    ticks = []
    engine = GoldPriceEngine(on_price_update_callback=lambda ts, p: ticks.append((ts, p)))
    engine.start()
    
    print("  Polling market data...")
    time.sleep(5)
    engine.stop()
    
    current_price = engine.get_current_price()
    print(f"  Received {len(ticks)} live price ticks.")
    print(f"  Current Gold Spot Price: ${current_price:.2f}" if current_price else "  Failed to fetch price")
    
    hist_df = engine.get_historical_data()
    print(f"  Historical Candles Retrieved: {len(hist_df)} rows")
    
    assert current_price is not None and current_price > 1000.0, "Invalid gold price"
    assert len(hist_df) > 0, "No historical candles retrieved"
    print("  >>> PASS: Feature 1 (Price Engine) working flawlessly!")
    return True


def test_feature_2_candle_builder() -> bool:
    print("\n" + "=" * 60)
    print("TEST 2: 10-Second Candle Builder")
    print("=" * 60)
    
    completed_candles = []
    builder = CandleBuilder(
        candle_interval_seconds=10,
        on_candle_complete_callback=lambda c: completed_candles.append(c)
    )
    
    base_time = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
    
    # Tick 1: at 12:00:01, price 4100.0
    builder.add_tick(base_time + timedelta(seconds=1), 4100.0)
    # Tick 2: at 12:00:05, price 4105.0 (High)
    builder.add_tick(base_time + timedelta(seconds=5), 4105.0)
    # Tick 3: at 12:00:08, price 4098.0 (Low)
    builder.add_tick(base_time + timedelta(seconds=8), 4098.0)
    # Tick 4: at 12:00:09, price 4102.0 (Close)
    builder.add_tick(base_time + timedelta(seconds=9), 4102.0)
    
    # Tick 5: at 12:00:11 (crosses into next 10s boundary) -> finalizes candle 1
    builder.add_tick(base_time + timedelta(seconds=11), 4103.0)
    
    assert len(completed_candles) == 1, f"Expected 1 finalized candle, got {len(completed_candles)}"
    c = completed_candles[0]
    print(f"  Candle 1 Finalized: Open={c.open_price}, High={c.high_price}, Low={c.low_price}, Close={c.close_price}, Ticks={c.tick_count}")
    
    assert c.open_price == 4100.0, f"Expected open 4100.0, got {c.open_price}"
    assert c.high_price == 4105.0, f"Expected high 4105.0, got {c.high_price}"
    assert c.low_price == 4098.0, f"Expected low 4098.0, got {c.low_price}"
    assert c.close_price == 4102.0, f"Expected close 4102.0, got {c.close_price}"
    assert c.tick_count == 4, f"Expected 4 ticks, got {c.tick_count}"
    
    print("  >>> PASS: Feature 2 (Candle Builder) working flawlessly!")
    return True


def test_feature_3_all_seven_agents() -> bool:
    print("\n" + "=" * 60)
    print("TEST 3: 7 Specialized Technical Analysis Agents")
    print("=" * 60)
    
    candles_df = generate_synthetic_candles(count=120, base_price=4100.0)
    
    agents = [
        RelativeStrengthIndexAgent(),
        MovingAverageConvergenceDivergenceAgent(),
        BollingerBandsAgent(),
        ExponentialMovingAverageCrossoverAgent(),
        StochasticOscillatorAgent(),
        AverageDirectionalIndexAgent(),
        IchimokuCloudAgent(),
    ]
    
    assert len(agents) == 7, "Must have exactly 7 agents"
    
    for i, agent in enumerate(agents, 1):
        signal = agent.analyze(candles_dataframe=candles_df)
        assert isinstance(signal, TradeSignal), f"Agent {agent.agent_name} did not return TradeSignal"
        assert signal.direction in (TradeDirection.CALL, TradeDirection.PUT, TradeDirection.NEUTRAL), "Invalid direction"
        assert 0.0 <= signal.confidence <= 1.0, f"Confidence out of range: {signal.confidence}"
        assert len(signal.reasoning) > 0, "Reasoning is empty"
        print(f"  [{i}/7] {agent.agent_name:40s} -> {signal.direction.value:7s} | Conf: {signal.confidence*100:4.1f}% | WinRate: {agent.get_success_rate()}%")
        print(f"        Reason: {signal.reasoning[:70]}...")
        
    print("  >>> PASS: Feature 3 (All 7 Agents) working flawlessly!")
    return True


def test_feature_4_consensus_engine() -> bool:
    print("\n" + "=" * 60)
    print("TEST 4: Consensus Engine (Unanimous 7/7 Rule)")
    print("=" * 60)
    
    agents = [
        RelativeStrengthIndexAgent(),
        MovingAverageConvergenceDivergenceAgent(),
        BollingerBandsAgent(),
        ExponentialMovingAverageCrossoverAgent(),
        StochasticOscillatorAgent(),
        AverageDirectionalIndexAgent(),
        IchimokuCloudAgent(),
    ]
    
    consensus_engine = ConsensusEngine(agents=agents, required_consensus_count=7)
    
    # Test A: Mixed market conditions
    candles_df = generate_synthetic_candles(count=80)
    res_mixed = consensus_engine.evaluate_market(candles_dataframe=candles_df)
    print(f"  Mixed Market Evaluation: Agreement={res_mixed.agreeing_agent_count}/7 | Consensus={res_mixed.consensus_reached}")
    
    # Test B: Simulated unanimous CALL
    class MockCallAgent(RelativeStrengthIndexAgent):
        def analyze(self, candles_dataframe, historical_dataframe=None):
            return TradeSignal(TradeDirection.CALL, 0.85, self.agent_name, "Strong Bullish", datetime.now())
            
    unanimous_call_agents = [MockCallAgent() for _ in range(7)]
    unanimous_engine = ConsensusEngine(agents=unanimous_call_agents, required_consensus_count=7)
    res_call = unanimous_engine.evaluate_market(candles_dataframe=candles_df)
    
    print(f"  Unanimous Test: Agreement={res_call.agreeing_agent_count}/7 | Consensus={res_call.consensus_reached} | Direction={res_call.direction.value}")
    assert res_call.consensus_reached is True, "Unanimous CALL must trigger consensus"
    assert res_call.direction == TradeDirection.CALL, "Direction must be CALL"
    assert res_call.agreeing_agent_count == 7, "Agreeing count must be 7"
    
    print("  >>> PASS: Feature 4 (Consensus Engine) working flawlessly!")
    return True


def test_feature_5_trade_executor() -> bool:
    print("\n" + "=" * 60)
    print("TEST 5: 1-Minute Trade Execution & 60-Second Settlement")
    print("=" * 60)
    
    executor = TradeExecutor(initial_balance=10000.0, payout_percentage=0.82)
    assert executor.current_balance == 10000.0, "Initial balance error"
    
    # 1. Place a 1-minute CALL trade
    trade_call = executor.place_trade(
        direction=TradeDirection.CALL,
        entry_price=4100.0,
        amount=1.0,
        agent_signals=[]
    )
    assert trade_call.result == "PENDING"
    assert trade_call.duration_seconds == 60
    assert executor.has_pending_trade() is True
    print(f"  Placed 1-Min Trade: ID={trade_call.trade_id[:8]} | Dir={trade_call.direction} | Entry=${trade_call.entry_price}")
    
    # 2. Settle as WIN (exit price 4105.0 > entry 4100.0)
    settled_win = executor.settle_trade(trade_call, exit_price=4105.0)
    assert settled_win.result == "WIN"
    assert settled_win.profit_loss == 0.82, f"Expected profit 0.82, got {settled_win.profit_loss}"
    assert executor.current_balance == 10000.82, f"Expected balance 10000.82, got {executor.current_balance}"
    print(f"  Settled Trade (WIN): Result={settled_win.result} | P&L=+${settled_win.profit_loss:.2f} | Balance=${executor.current_balance:.2f}")
    
    # 3. Place a 1-minute PUT trade
    trade_put = executor.place_trade(
        direction=TradeDirection.PUT,
        entry_price=4105.0,
        amount=1.0,
        agent_signals=[]
    )
    # Settle as LOSS (exit price 4108.0 > entry 4105.0 for PUT)
    settled_loss = executor.settle_trade(trade_put, exit_price=4108.0)
    assert settled_loss.result == "LOSS"
    assert settled_loss.profit_loss == -1.0, f"Expected loss -1.0, got {settled_loss.profit_loss}"
    assert executor.current_balance == 9999.82, f"Expected balance 9999.82, got {executor.current_balance}"
    print(f"  Settled Trade (LOSS): Result={settled_loss.result} | P&L=-${abs(settled_loss.profit_loss):.2f} | Balance=${executor.current_balance:.2f}")
    
    print("  >>> PASS: Feature 5 (Trade Execution & 60s Settlement) working flawlessly!")
    return True


def test_feature_6_performance_tracker() -> bool:
    print("\n" + "=" * 60)
    print("TEST 6: Performance & Individual Agent Success Rate Tracker")
    print("=" * 60)
    
    tracker = PerformanceTracker(initial_balance=10000.0)
    executor = TradeExecutor(initial_balance=10000.0, payout_percentage=0.82)
    
    # Execute 3 trades: 2 wins, 1 loss (66.7% win rate)
    t1 = executor.place_trade(TradeDirection.CALL, 4100.0, 1.0, [])
    s1 = executor.settle_trade(t1, 4102.0) # Win
    tracker.record_trade(s1)
    
    t2 = executor.place_trade(TradeDirection.PUT, 4102.0, 1.0, [])
    s2 = executor.settle_trade(t2, 4100.0) # Win
    tracker.record_trade(s2)
    
    t3 = executor.place_trade(TradeDirection.CALL, 4100.0, 1.0, [])
    s3 = executor.settle_trade(t3, 4099.0) # Loss
    tracker.record_trade(s3)
    
    stats = tracker.get_overall_statistics()
    print(f"  Total Trades: {stats['total_trades']}")
    print(f"  Winning Trades: {stats['winning_trades']}, Losing: {stats['losing_trades']}")
    print(f"  Success Rate: {stats['success_rate']*100:.1f}%")
    print(f"  Total P&L: ${stats['total_profit_loss']:.2f}")
    print(f"  Balance: ${stats['current_balance']:.2f}")
    
    assert stats['total_trades'] == 3
    assert stats['winning_trades'] == 2
    assert stats['losing_trades'] == 1
    assert round(stats['success_rate'], 2) == 0.67
    
    # Test individual agent stats recording
    agent = RelativeStrengthIndexAgent()
    agent.record_prediction_result(TradeDirection.CALL, was_correct=True)
    agent.record_prediction_result(TradeDirection.CALL, was_correct=True)
    agent.record_prediction_result(TradeDirection.PUT, was_correct=False)
    
    agent_stats = agent.get_statistics()
    print(f"  Individual Agent ({agent.agent_name}) Stats: Total={agent_stats['total_predictions']}, Success Rate={agent_stats['success_rate']}%")
    assert agent_stats['total_predictions'] == 3
    assert agent_stats['correct_predictions'] == 2
    assert agent_stats['success_rate'] == 66.67
    
    print("  >>> PASS: Feature 6 (Performance & Individual Stats) working flawlessly!")
    return True


def test_feature_7_rest_api() -> bool:
    print("\n" + "=" * 60)
    print("TEST 7: REST API Endpoints Verification")
    print("=" * 60)
    
    import requests
    base_url = "http://127.0.0.1:5000"
    
    endpoints = [
        ("/api/status", 200),
        ("/api/state", 200),
        ("/api/price", 200),
        ("/api/candles", 200),
        ("/api/signals", 200),
        ("/api/performance", 200),
        ("/api/trades", 200),
    ]
    
    # Try live connection first; if server not running, use Flask test client
    use_live_server = False
    try:
        import requests
        base_url = "http://127.0.0.1:5000"
        probe = requests.get(f"{base_url}/api/status", timeout=1)
        if probe.status_code == 200:
            use_live_server = True
    except Exception:
        use_live_server = False
        
    if use_live_server:
        print("  Connected to live running dashboard server.")
        for ep, expected_code in endpoints:
            res = requests.get(f"{base_url}{ep}", timeout=3)
            assert res.status_code == expected_code, f"Endpoint {ep} returned {res.status_code}"
            json_data = res.json()
            print(f"  GET {ep:20s} -> HTTP {res.status_code} | Payload keys: {list(json_data.keys()) if isinstance(json_data, dict) else len(json_data)}")
    else:
        print("  Live server not detected — verifying REST endpoints via internal Flask test client.")
        from dashboard.app import create_dashboard_application
        mock_state = {
            "current_price": 4100.50,
            "price_timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "candles": [{"time": 1700000000, "open": 4100.0, "high": 4102.0, "low": 4099.0, "close": 4101.0}],
            "agent_signals": [],
            "consensus": {},
            "performance": {"total_trades": 0},
            "recent_trades": [],
            "active_trade": None,
        }
        app, _ = create_dashboard_application(
            get_state_callback=lambda: mock_state,
            get_config_callback=lambda: {"candle_interval_seconds": 10},
            update_config_callback=lambda cfg: cfg,
        )
        test_client = app.test_client()
        for ep, expected_code in endpoints:
            res = test_client.get(ep)
            assert res.status_code == expected_code, f"Endpoint {ep} returned {res.status_code}"
            json_data = res.get_json()
            print(f"  GET {ep:20s} -> HTTP {res.status_code} | Payload keys: {list(json_data.keys()) if isinstance(json_data, dict) else len(json_data)}")
        
    print("  >>> PASS: Feature 7 (REST API Endpoints) working flawlessly!")
    return True


def test_feature_8_olymptrade_client() -> bool:
    print("\n" + "=" * 60)
    print("TEST 8: Olymp Trade Integration Client")
    print("=" * 60)
    
    client = OlympTradeClient(use_simulated_mode=True)
    assert client.is_simulated is True
    print(f"  Client initial mode: Simulated Demo={client.is_simulated}")
    
    order = client.place_demo_trade(
        asset_symbol="gold",
        direction="CALL",
        amount_usd=1.0,
        duration_seconds=60
    )
    
    assert order["status"] == "success"
    assert order["direction"] == "CALL"
    assert order["amount"] == 1.0
    assert order["duration"] == 60
    print(f"  Order placed via OlympTradeClient: OrderID={order['order_id']} | Asset={order['asset']} | Dir={order['direction']} | Duration={order['duration']}s")
    
    client.set_credentials(auth_token="demo_test_token_xyz")
    assert client.is_connected is True
    print("  Live credentials configure test: Connected=True")
    
    print("  >>> PASS: Feature 8 (Olymp Trade Client) working flawlessly!")
    return True


def run_full_feature_test_suite():
    print("\n" + "#" * 70)
    print("  GOLD TRADING ANALYSIS PLATFORM — FEATURE-BY-FEATURE TEST SUITE")
    print("#" * 70)
    
    all_passed = True
    tests = [
        test_feature_1_price_engine,
        test_feature_2_candle_builder,
        test_feature_3_all_seven_agents,
        test_feature_4_consensus_engine,
        test_feature_5_trade_executor,
        test_feature_6_performance_tracker,
        test_feature_7_rest_api,
        test_feature_8_olymptrade_client,
    ]
    
    for test_fn in tests:
        try:
            ok = test_fn()
            if not ok:
                all_passed = False
        except Exception as e:
            print(f"  FAILED: {test_fn.__name__} raised: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
            
    print("\n" + "#" * 70)
    if all_passed:
        print("  ALL 8 CORE FEATURES TESTED & VERIFIED WITH 100% SUCCESS!")
    else:
        print("  SOME TESTS ENCOUNTERED FAILURES.")
    print("#" * 70 + "\n")


if __name__ == "__main__":
    run_full_feature_test_suite()
