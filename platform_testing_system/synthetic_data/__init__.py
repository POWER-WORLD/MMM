"""
Synthetic Data Generation Subsystem.

Provides generators for realistic market regimes, streaming price ticks,
anomalous and corrupted datasets, and mock network response payloads.
"""

from platform_testing_system.synthetic_data.market_regimes import (
    MarketRegimeGenerator,
    MarketRegimeType,
)
from platform_testing_system.synthetic_data.tick_generator import (
    PriceTickGenerator,
    TickPatternType,
)
from platform_testing_system.synthetic_data.anomaly_generator import (
    AnomalyDataGenerator,
    AnomalyType,
)
from platform_testing_system.synthetic_data.mock_network_data import (
    MockNetworkDataFactory,
)

__all__ = [
    "MarketRegimeGenerator",
    "MarketRegimeType",
    "PriceTickGenerator",
    "TickPatternType",
    "AnomalyDataGenerator",
    "AnomalyType",
    "MockNetworkDataFactory",
]
