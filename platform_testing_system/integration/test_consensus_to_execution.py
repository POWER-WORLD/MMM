"""
Integration Tests for Consensus to Trade Execution and Settlement Pipeline.

Verifies the lifecycle from consensus decision -> trade placement -> 60-second settlement
-> performance recording -> multi-agent accuracy tracking.
"""

from typing import List
import pytest

from agents.base_agent import BaseAnalysisAgent, TradeDirection, TradeSignal
from agents.consensus_engine import ConsensusEngine
from agents.rsi_agent import RelativeStrengthIndexAgent
from trading.performance_tracker import PerformanceTracker
from trading.trade_executor import TradeExecutor


class TestConsensusToExecutionPipeline:
    """Pipeline integration test: Consensus Decision -> Execution -> Settlement -> Performance."""

    def test_complete_trade_placement_and_settlement_pipeline(self) -> None:
        """
        Execute full trading pipeline:
        1. 7 agents reach unanimous CALL consensus.
        2. TradeExecutor places 1-minute CALL trade at entry $4100.0 with $10.0 stake.
        3. Trade settles as WIN at exit $4104.50.
        4. PerformanceTracker updates metrics (+$8.20 PnL).
        5. ConsensusEngine updates agent accuracy stats (1/1 = 100%).
        """
        # Step 1: Consensus
        class UnanimousBullAgent(RelativeStrengthIndexAgent):
            def __init__(self, name: str):
                super().__init__()
                self.agent_name = name

            def analyze(self, candles_dataframe, historical_dataframe=None):
                return TradeSignal(
                    direction=TradeDirection.CALL,
                    confidence=0.85,
                    agent_name=self.agent_name,
                    reasoning="Unanimous bullish confirmation",
                    timestamp=None,
                )

        agents: List[BaseAnalysisAgent] = [UnanimousBullAgent(f"Agent_{i}") for i in range(7)]
        consensus_engine = ConsensusEngine(agents=agents, required_consensus_count=7)

        result = consensus_engine.evaluate_market(candles_dataframe=None)
        assert result.consensus_reached is True
        assert result.direction == TradeDirection.CALL

        # Step 2: Trade Placement
        executor = TradeExecutor(initial_balance=10000.0, payout_percentage=0.82)
        tracker = PerformanceTracker(initial_balance=10000.0)

        entry_price = 4100.0
        stake = 10.0
        trade = executor.place_trade(
            direction=result.direction,
            entry_price=entry_price,
            amount=stake,
            agent_signals=result.signals,
            duration_seconds=60,
        )

        assert trade.result == "PENDING"
        assert executor.has_pending_trade() is True

        # Step 3: Trade Settlement (WIN: exit > entry for CALL)
        exit_price = 4104.50
        settled_trade = executor.settle_trade(trade_record=trade, exit_price=exit_price)
        assert settled_trade.result == "WIN"
        assert settled_trade.profit_loss == 8.20
        assert executor.current_balance == 10008.20
        assert executor.has_pending_trade() is False

        # Step 4: Record in Performance Tracker
        tracker.record_trade(trade_record=settled_trade)
        stats = tracker.get_overall_statistics()
        assert stats["total_trades"] == 1
        assert stats["winning_trades"] == 1
        assert stats["success_rate"] == 1.0  # 100% decimal
        assert stats["total_profit_loss"] == 8.20
        assert stats["current_balance"] == 10008.20

        # Step 5: Update Agent Accuracy
        consensus_engine.record_trade_result(
            direction=TradeDirection.CALL,
            was_correct=True,
        )
        agent_stats = consensus_engine.get_all_agent_statistics()
        assert len(agent_stats) == 7
        for a_stat in agent_stats:
            assert a_stat["total_predictions"] == 1
            assert a_stat["correct_predictions"] == 1
            assert a_stat["success_rate"] == 100.0
