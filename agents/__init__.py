"""
Analysis Agents module for the Gold Trading Analysis Platform.

Contains 7 specialized technical analysis agents and the consensus engine:
- RelativeStrengthIndexAgent (RSI)
- MovingAverageConvergenceDivergenceAgent (MACD)
- BollingerBandsAgent (Bollinger Bands)
- ExponentialMovingAverageCrossoverAgent (EMA Crossover)
- StochasticOscillatorAgent (Stochastic Oscillator)
- AverageDirectionalIndexAgent (ADX)
- IchimokuCloudAgent (Ichimoku Cloud)
- ConsensusEngine (Aggregates all 7 agent signals)
"""

from agents.base_agent import (
    BaseAnalysisAgent,
    TradeDirection,
    TradeSignal,
)
from agents.rsi_agent import RelativeStrengthIndexAgent
from agents.macd_agent import MovingAverageConvergenceDivergenceAgent
from agents.bollinger_agent import BollingerBandsAgent
from agents.ema_crossover_agent import ExponentialMovingAverageCrossoverAgent
from agents.stochastic_agent import StochasticOscillatorAgent
from agents.adx_agent import AverageDirectionalIndexAgent
from agents.ichimoku_agent import IchimokuCloudAgent
from agents.consensus_engine import ConsensusEngine, ConsensusResult

__all__ = [
    "BaseAnalysisAgent",
    "TradeDirection",
    "TradeSignal",
    "RelativeStrengthIndexAgent",
    "MovingAverageConvergenceDivergenceAgent",
    "BollingerBandsAgent",
    "ExponentialMovingAverageCrossoverAgent",
    "StochasticOscillatorAgent",
    "AverageDirectionalIndexAgent",
    "IchimokuCloudAgent",
    "ConsensusEngine",
    "ConsensusResult",
]
