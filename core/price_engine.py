"""
Real-Time Gold Price Fetching Engine Module.

Provides the GoldPriceEngine class that continuously streams live spot Gold (XAU/USD)
prices using high-frequency institutional endpoints (Binance PAXG Spot Gold)
with seamless failover to Yahoo Finance Gold Futures (GC=F).

Runs a dedicated background thread polling every 1 second to deliver live tick
updates, build real-time candles, and serve historical intraday data for multi-agent
technical analysis.
"""

import logging
import threading
from datetime import datetime, timezone
from typing import Callable, Final, Optional

import pandas as pd
import requests
import yfinance as yf

from config import PLATFORM_CONFIG

logger: Final[logging.Logger] = logging.getLogger(__name__)

USER_AGENT_STRING: Final[str] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT_SECONDS: Final[int] = 4


class GoldPriceEngine:
    """Real-time gold price fetching engine.

    Continuously polls spot Gold prices (PAXG/USDT primary, GC=F fallback)
    on a 1-second interval and delivers price updates via a callback function.
    Maintains the most recently fetched price for synchronous access.

    Attributes:
        _ticker_symbol: The ticker symbol for gold futures (GC=F).
        _poll_interval_seconds: Seconds between consecutive price polls (1s).
        _historical_data_period: Look-back period for historical data fetch.
        _historical_data_interval: Bar interval for historical data fetch.
        _on_price_update_callback: Callable invoked with (timestamp, price).
        _current_price: Most recently fetched gold price, or None.
        _stop_event: Threading event used to signal the polling thread.
        _polling_thread: The background thread running the price poll loop.
        _http_session: Reusable requests session with standard headers.
    """

    def __init__(
        self,
        on_price_update_callback: Callable[[datetime, float], None],
        poll_interval_seconds: Optional[float] = None,
        http_session: Optional[requests.Session] = None,
    ) -> None:
        """Initialize the GoldPriceEngine.

        Args:
            on_price_update_callback: A callable that receives two arguments:
                - timestamp (datetime): The UTC time of the price observation.
                - price (float): The latest gold price in USD.
            poll_interval_seconds: Optional custom polling interval (defaults to 1.0s).
            http_session: Optional custom or mock requests.Session instance.
        """
        price_engine_config = PLATFORM_CONFIG.price_engine

        self._ticker_symbol: str = price_engine_config.GOLD_TICKER_SYMBOL
        # Use 1-second polling for true live streaming or custom interval
        self._poll_interval_seconds: float = poll_interval_seconds if poll_interval_seconds is not None else 1.0
        self._historical_data_period: str = price_engine_config.HISTORICAL_DATA_PERIOD
        self._historical_data_interval: str = price_engine_config.HISTORICAL_DATA_INTERVAL

        self._on_price_update_callback: Callable[[datetime, float], None] = on_price_update_callback

        self._ticker: yf.Ticker = yf.Ticker(self._ticker_symbol)
        self._current_price: Optional[float] = None
        self._stop_event: threading.Event = threading.Event()
        self._polling_thread: Optional[threading.Thread] = None

        if http_session is not None:
            self._http_session: requests.Session = http_session
        else:
            self._http_session: requests.Session = requests.Session()
            self._http_session.headers.update({"User-Agent": USER_AGENT_STRING})

        logger.info(
            "GoldPriceEngine initialized — Spot Gold Live Stream (%.1fs tick interval)",
            self._poll_interval_seconds,
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the background price-polling thread."""
        if self._polling_thread is not None and self._polling_thread.is_alive():
            logger.warning("GoldPriceEngine is already running — ignoring start request.")
            return

        self._stop_event.clear()
        self._polling_thread = threading.Thread(
            target=self._polling_loop,
            name="GoldPriceEngine-PollingThread",
            daemon=True,
        )
        self._polling_thread.start()
        logger.info("GoldPriceEngine polling thread started.")

    def stop(self) -> None:
        """Stop the background price-polling thread gracefully."""
        if self._polling_thread is None or not self._polling_thread.is_alive():
            logger.warning("GoldPriceEngine is not running — ignoring stop request.")
            return

        logger.info("Stopping GoldPriceEngine polling thread...")
        self._stop_event.set()

        join_timeout_seconds: float = self._poll_interval_seconds * 2.0 + 3.0
        self._polling_thread.join(timeout=join_timeout_seconds)

        if self._polling_thread.is_alive():
            logger.error("GoldPriceEngine polling thread did not terminate within %.1fs.", join_timeout_seconds)
        else:
            logger.info("GoldPriceEngine polling thread stopped successfully.")

    def get_current_price(self) -> Optional[float]:
        """Return the most recently fetched gold price."""
        return self._current_price

    def get_historical_data(self) -> pd.DataFrame:
        """Fetch historical intraday OHLCV data for gold.

        Retrieves data with multi-source fallback:
        1. Binance PAXGUSDT 1-second/1-minute genuine spot candles
        2. Yahoo Finance direct v8 chart API
        3. yfinance historical data
        """
        standard_columns = ["timestamp", "open", "high", "low", "close", "volume"]

        # 1. Primary: Binance PAXG/USDT (Exact Spot Gold)
        try:
            url = "https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval=1m&limit=300"
            resp = self._http_session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            if resp.status_code == 200:
                raw_klines = resp.json()
                if raw_klines and len(raw_klines) > 10:
                    rows = []
                    for k in raw_klines:
                        ts = datetime.fromtimestamp(k[0] / 1000.0, tz=timezone.utc)
                        rows.append({
                            "timestamp": ts,
                            "open": float(k[1]),
                            "high": float(k[2]),
                            "low": float(k[3]),
                            "close": float(k[4]),
                            "volume": float(k[5]),
                        })
                    df = pd.DataFrame(rows).dropna()
                    if not df.empty:
                        logger.info("Historical data fetched via Binance Spot Gold — %d rows.", len(df))
                        return df
        except Exception as binance_err:
            logger.debug("Binance historical fetch notice: %s — trying Yahoo Finance.", binance_err)

        # 2. Secondary: Yahoo Finance direct chart API
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{self._ticker_symbol}?interval=1m&range=1d"
            response = self._http_session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)

            if response.status_code == 200:
                payload = response.json()
                results = payload.get("chart", {}).get("result")
                if results and len(results) > 0:
                    data = results[0]
                    raw_timestamps = data.get("timestamp", [])
                    indicators = data.get("indicators", {}).get("quote", [{}])[0]

                    if raw_timestamps and indicators:
                        timestamps = [
                            datetime.fromtimestamp(ts, tz=timezone.utc)
                            for ts in raw_timestamps
                        ]
                        df = pd.DataFrame({
                            "timestamp": timestamps,
                            "open": indicators.get("open", []),
                            "high": indicators.get("high", []),
                            "low": indicators.get("low", []),
                            "close": indicators.get("close", []),
                            "volume": indicators.get("volume", []),
                        }).dropna()

                        if not df.empty:
                            logger.info("Historical data fetched via Yahoo API — %d rows.", len(df))
                            return df
        except Exception as api_err:
            logger.debug("Direct API historical fetch error: %s — falling back to yfinance.", api_err)

        # 3. Tertiary: yfinance
        try:
            historical_dataframe = self._ticker.history(period="1d", interval="1m")
            if not historical_dataframe.empty:
                historical_dataframe = historical_dataframe.reset_index()
                column_mapping = {
                    "Datetime": "timestamp",
                    "Date": "timestamp",
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Volume": "volume",
                }
                historical_dataframe = historical_dataframe.rename(columns=column_mapping)
                available_columns = [
                    col for col in standard_columns if col in historical_dataframe.columns
                ]
                return historical_dataframe[available_columns]
        except Exception:
            pass

        return pd.DataFrame(columns=standard_columns)

    # ------------------------------------------------------------------
    # Internal methods
    # ------------------------------------------------------------------

    def _polling_loop(self) -> None:
        """Run the continuous 1-second price-polling loop on the background thread."""
        logger.info("Price polling loop started (1s live tick interval).")

        while not self._stop_event.is_set():
            try:
                fetched_price: Optional[float] = self._fetch_current_price()

                if fetched_price is not None:
                    observation_timestamp: datetime = datetime.now(tz=timezone.utc)
                    self._current_price = fetched_price

                    try:
                        self._on_price_update_callback(observation_timestamp, fetched_price)
                    except Exception:
                        logger.exception(
                            "Exception in on_price_update_callback for price=%.4f.",
                            fetched_price,
                        )
                else:
                    logger.debug("Price fetch returned None — skipping callback.")

            except Exception:
                logger.exception("Unexpected error in price polling loop iteration.")

            self._stop_event.wait(timeout=self._poll_interval_seconds)

        logger.info("Price polling loop exited.")

    def _fetch_current_price(self) -> Optional[float]:
        """Fetch the latest spot gold price.

        Primary: Binance Spot Gold (PAXGUSDT) - real-time sub-second updates
        Secondary: Yahoo Finance chart API for GC=F
        Tertiary: yfinance fast_info
        """
        # ----- 1. Primary: Binance Spot Gold (PAXGUSDT) -----
        try:
            url = "https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT"
            res = self._http_session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            if res.status_code == 200:
                data = res.json()
                price_val = float(data["price"])
                logger.debug("Spot Gold fetched via Binance: %.2f", price_val)
                return price_val
        except Exception as binance_err:
            logger.debug("Binance spot price fetch error: %s — trying Yahoo.", binance_err)

        # ----- 2. Secondary: Kraken Institutional Gold Spot (PAXG/USD) -----
        try:
            url = "https://api.kraken.com/0/public/Ticker?pair=PAXGUSD"
            res = self._http_session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            if res.status_code == 200:
                payload = res.json()
                pair_data = payload.get("result", {}).get("PAXGUSD", {})
                last_trade = pair_data.get("c", [])
                if last_trade and len(last_trade) > 0:
                    price_val = float(last_trade[0])
                    logger.debug("Spot Gold fetched via Kraken: %.2f", price_val)
                    return price_val
        except Exception as kraken_err:
            logger.debug("Kraken spot price fetch notice: %s — trying Yahoo Finance.", kraken_err)

        # ----- 3. Tertiary: Yahoo Finance chart quote -----
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{self._ticker_symbol}?interval=1m&range=1d"
            response = self._http_session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            if response.status_code == 200:
                payload = response.json()
                results = payload.get("chart", {}).get("result")
                if results and len(results) > 0:
                    meta = results[0].get("meta", {})
                    market_price = meta.get("regularMarketPrice")
                    if market_price is not None:
                        return float(market_price)
        except Exception as direct_err:
            logger.debug("Yahoo direct API price fetch error: %s", direct_err)

        # ----- 4. Quaternary: yfinance fast_info -----
        try:
            fast_info = self._ticker.fast_info
            last_price = fast_info.get("lastPrice")
            if last_price is not None and isinstance(last_price, (int, float)):
                return float(last_price)
        except Exception:
            pass

        return None
