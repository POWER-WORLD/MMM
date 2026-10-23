"""
Adversarial and Anomalous Data Generator.

Produces corrupted, malformed, edge-case, and adversarial market datasets
to stress-test indicator robustness, error handling, and platform resilience.
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd


class AnomalyType(Enum):
    """Enumeration of data anomaly scenarios."""

    EMPTY_DATAFRAME = "EMPTY_DATAFRAME"
    SINGLE_ROW_DATAFRAME = "SINGLE_ROW_DATAFRAME"
    INSUFFICIENT_ROWS = "INSUFFICIENT_ROWS"
    MISSING_CLOSE_COLUMN = "MISSING_CLOSE_COLUMN"
    MISSING_ALL_PRICE_COLUMNS = "MISSING_ALL_PRICE_COLUMNS"
    ALL_NAN_VALUES = "ALL_NAN_VALUES"
    INTERMITTENT_NANS = "INTERMITTENT_NANS"
    ZERO_PRICES = "ZERO_PRICES"
    NEGATIVE_PRICES = "NEGATIVE_PRICES"
    INVERTED_HIGH_LOW = "INVERTED_HIGH_LOW"
    EXTREME_SPIKE_OUTLIER = "EXTREME_SPIKE_OUTLIER"
    DUPLICATE_TIMESTAMPS = "DUPLICATE_TIMESTAMPS"
    NON_CHRONOLOGICAL_TIMESTAMPS = "NON_CHRONOLOGICAL_TIMESTAMPS"
    ZERO_VOLUME = "ZERO_VOLUME"
    STRING_DATA_TYPES = "STRING_DATA_TYPES"
    INFINITE_VALUES = "INFINITE_VALUES"


class AnomalyDataGenerator:
    """Factory generating adversarial dataframes for resilience testing."""

    @classmethod
    def generate_anomaly(
        cls,
        anomaly: AnomalyType,
        count: int = 60,
        base_price: float = 4100.0,
        random_seed: int = 42,
    ) -> pd.DataFrame:
        """
        Generate a DataFrame exhibiting the specified anomaly condition.

        Args:
            anomaly: Target AnomalyType.
            count: Number of rows to generate.
            base_price: Nominal price level.
            random_seed: Random seed for reproducibility.

        Returns:
            pandas.DataFrame configured with the designated anomaly.
        """
        np.random.seed(random_seed)
        now = datetime.now(tz=timezone.utc)
        timestamps = [now - timedelta(seconds=10 * (count - 1 - i)) for i in range(count)]

        if anomaly == AnomalyType.EMPTY_DATAFRAME:
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

        if anomaly == AnomalyType.SINGLE_ROW_DATAFRAME:
            return pd.DataFrame([{
                "timestamp": now,
                "open": base_price,
                "high": base_price + 0.5,
                "low": base_price - 0.5,
                "close": base_price,
                "volume": 50,
            }])

        if anomaly == AnomalyType.INSUFFICIENT_ROWS:
            # Platform requires at least 30 candles; return 10
            sub_count = 10
            sub_ts = timestamps[:sub_count]
            return pd.DataFrame({
                "timestamp": sub_ts,
                "open": [base_price] * sub_count,
                "high": [base_price + 0.2] * sub_count,
                "low": [base_price - 0.2] * sub_count,
                "close": [base_price] * sub_count,
                "volume": [10] * sub_count,
            })

        # Base valid frame for mutation
        df = cls._create_clean_frame(timestamps, count, base_price)

        if anomaly == AnomalyType.MISSING_CLOSE_COLUMN:
            return df.drop(columns=["close"])

        if anomaly == AnomalyType.MISSING_ALL_PRICE_COLUMNS:
            return df[["timestamp", "volume"]]

        if anomaly == AnomalyType.ALL_NAN_VALUES:
            df["close"] = np.nan
            df["high"] = np.nan
            df["low"] = np.nan
            df["open"] = np.nan
            return df

        if anomaly == AnomalyType.INTERMITTENT_NANS:
            # Inject NaNs at random indices in close and high
            nan_indices = np.random.choice(count, size=count // 5, replace=False)
            df.loc[nan_indices, "close"] = np.nan
            return df

        if anomaly == AnomalyType.ZERO_PRICES:
            df["close"] = 0.0
            df["open"] = 0.0
            df["high"] = 0.0
            df["low"] = 0.0
            return df

        if anomaly == AnomalyType.NEGATIVE_PRICES:
            df["close"] = -base_price
            df["open"] = -base_price
            df["high"] = -base_price + 1.0
            df["low"] = -base_price - 1.0
            return df

        if anomaly == AnomalyType.INVERTED_HIGH_LOW:
            # High is lower than low
            df["high"] = df["low"] - 2.0
            return df

        if anomaly == AnomalyType.EXTREME_SPIKE_OUTLIER:
            # Single bar spike of $50,000
            spike_idx = count // 2
            df.loc[spike_idx, "high"] = 55000.0
            df.loc[spike_idx, "close"] = 54900.0
            return df

        if anomaly == AnomalyType.DUPLICATE_TIMESTAMPS:
            # Clone timestamp of row 0 across multiple rows
            df.loc[1:5, "timestamp"] = df.loc[0, "timestamp"]
            return df

        if anomaly == AnomalyType.NON_CHRONOLOGICAL_TIMESTAMPS:
            # Shuffle timestamp column
            df["timestamp"] = np.random.permutation(df["timestamp"].values)
            return df

        if anomaly == AnomalyType.ZERO_VOLUME:
            df["volume"] = 0
            return df

        if anomaly == AnomalyType.STRING_DATA_TYPES:
            df["close"] = df["close"].astype(str)
            df["open"] = "INVALID_PRICE"
            return df

        if anomaly == AnomalyType.INFINITE_VALUES:
            df.loc[count // 3, "close"] = np.inf
            df.loc[count // 2, "high"] = -np.inf
            return df

        return df

    @staticmethod
    def _create_clean_frame(timestamps, count: int, base_price: float) -> pd.DataFrame:
        """Create standard baseline dataframe."""
        records = []
        p = base_price
        for i in range(count):
            p += np.random.normal(0, 0.2)
            records.append({
                "timestamp": timestamps[i],
                "open": round(p - 0.1, 4),
                "high": round(p + 0.3, 4),
                "low": round(p - 0.3, 4),
                "close": round(p, 4),
                "volume": 50,
            })
        return pd.DataFrame(records)
