"""
Mock Network Data and API Response Payload Factory.

Provides institutional-grade schema-valid mock payloads for:
- Binance PAXG/USDT spot price & klines APIs
- Kraken PAXG/USD public ticker API
- Yahoo Finance v8 chart API (GC=F)
- Olymp Trade demo execution & balance APIs
- MockResponse helper for requests.Session interception
"""

import time
from typing import Any, Dict, List, Optional


class MockHttpResponse:
    """Mock requests.Response object for deterministic offline testing."""

    def __init__(
        self,
        json_data: Optional[Any] = None,
        status_code: int = 200,
        text_content: Optional[str] = None,
    ) -> None:
        self._json_data: Any = json_data
        self.status_code: int = status_code
        self.text: str = text_content if text_content is not None else (str(json_data) if json_data is not None else "")
        self.content: bytes = self.text.encode("utf-8")

    def json(self) -> Any:
        if self._json_data is not None:
            return self._json_data
        raise ValueError("No JSON payload provided in mock response")


class MockNetworkDataFactory:
    """Factory generating realistic API responses for external endpoints."""

    @staticmethod
    def create_binance_price_payload(price: float = 4105.50, symbol: str = "PAXGUSDT") -> Dict[str, Any]:
        """Generate Binance ticker price response."""
        return {
            "symbol": symbol,
            "price": f"{price:.2f}",
        }

    @staticmethod
    def create_binance_klines_payload(
        count: int = 60,
        base_price: float = 4100.0,
        interval_ms: int = 60000,
    ) -> List[List[Any]]:
        """Generate Binance klines array format."""
        current_time_ms = int(time.time() * 1000)
        klines = []
        p = base_price

        for i in range(count):
            open_time = current_time_ms - ((count - i) * interval_ms)
            close_time = open_time + interval_ms - 1
            o = p
            h = p + 0.8
            l = p - 0.8
            c = p + 0.2
            v = 15.5
            klines.append([
                open_time,
                f"{o:.4f}",
                f"{h:.4f}",
                f"{l:.4f}",
                f"{c:.4f}",
                f"{v:.2f}",
                close_time,
                "63550.00",
                42,
                "8.2",
                "33600.00",
                "0",
            ])
            p = c

        return klines

    @staticmethod
    def create_kraken_ticker_payload(price: float = 4105.50) -> Dict[str, Any]:
        """Generate Kraken ticker API payload."""
        return {
            "error": [],
            "result": {
                "PAXGUSD": {
                    "a": [f"{price + 0.10:.2f}", "10", "10"],
                    "b": [f"{price - 0.10:.2f}", "10", "10"],
                    "c": [f"{price:.2f}", "0.5"],
                    "v": ["120.4", "450.2"],
                    "p": [f"{price:.2f}", f"{price:.2f}"],
                    "t": [150, 480],
                    "l": [f"{price - 15.0:.2f}", f"{price - 20.0:.2f}"],
                    "h": [f"{price + 15.0:.2f}", f"{price + 20.0:.2f}"],
                    "o": f"{price - 5.0:.2f}",
                }
            },
        }

    @staticmethod
    def create_yahoo_chart_payload(
        ticker: str = "GC=F",
        price: float = 4105.50,
        count: int = 60,
    ) -> Dict[str, Any]:
        """Generate Yahoo Finance v8 chart API payload."""
        now_epoch = int(time.time())
        timestamps = [now_epoch - (count - i) * 60 for i in range(count)]
        opens = [price - 0.2 + (i * 0.05) for i in range(count)]
        highs = [p + 0.5 for p in opens]
        lows = [p - 0.5 for p in opens]
        closes = [p + 0.1 for p in opens]
        volumes = [100 for _ in range(count)]

        return {
            "chart": {
                "result": [
                    {
                        "meta": {
                            "currency": "USD",
                            "symbol": ticker,
                            "regularMarketPrice": price,
                            "chartPreviousClose": price - 1.0,
                        },
                        "timestamp": timestamps,
                        "indicators": {
                            "quote": [
                                {
                                    "open": opens,
                                    "high": highs,
                                    "low": lows,
                                    "close": closes,
                                    "volume": volumes,
                                }
                            ]
                        },
                    }
                ],
                "error": None,
            }
        }

    @staticmethod
    def create_olymp_trade_order_payload(
        order_id: str = "ot_order_9988",
        asset: str = "gold",
        direction: str = "CALL",
        amount: float = 1.0,
        duration: int = 60,
    ) -> Dict[str, Any]:
        """Generate successful Olymp Trade order confirmation."""
        return {
            "status": "success",
            "order_id": order_id,
            "asset": asset,
            "direction": direction,
            "amount": amount,
            "duration": duration,
            "timestamp": int(time.time()),
        }

    @staticmethod
    def create_olymp_trade_error_payload(message: str = "Insufficient balance") -> Dict[str, Any]:
        """Generate failed Olymp Trade order payload."""
        return {
            "status": "error",
            "message": message,
            "code": 4001,
        }
