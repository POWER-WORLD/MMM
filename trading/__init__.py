"""
Trading module for the Gold Trading Analysis Platform.

Contains trade execution, performance tracking, and broker connectivity:
- TradeExecutor: Simulated trade execution with 1-minute settlement
- PerformanceTracker: Win rates, profit/loss tracking, and streaks
- OlympTradeClient: Direct Olymp Trade demo account execution
"""

from trading.trade_executor import TradeExecutor, TradeRecord
from trading.performance_tracker import PerformanceTracker
from trading.olymptrade_client import OlympTradeClient

__all__ = [
    "TradeExecutor",
    "TradeRecord",
    "PerformanceTracker",
    "OlympTradeClient",
]
