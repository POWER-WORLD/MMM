"""
Olymp Trade Account & Trade Execution Connector Module.

Provides integration capabilities with Olymp Trade for demo trade execution:
- Session authentication via user token / API credentials
- Fixed Time Trading (FTT) 1-minute gold contract execution
- Account balance and trade status synchronization
- Seamless switching between local simulated demo and live Olymp Trade demo account
"""

import logging
import json
import threading
import time
from datetime import datetime, timezone
from typing import Callable, Dict, Final, Optional

import requests

logger: Final[logging.Logger] = logging.getLogger(__name__)


class OlympTradeClient:
    """Client for executing Fixed Time Trades on Olymp Trade demo accounts.

    Supports account authentication, real-time balance queries, and
    executing 1-minute fixed-time trades on gold (XAU/USD / GC=F).

    Attributes:
        _auth_token: Olymp Trade user session token or API token.
        _account_id: Demo account identifier.
        _is_connected: Connection status flag.
        _demo_balance: Current demo account balance.
        _base_url: Olymp Trade API base endpoint.
    """

    DEFAULT_BASE_URL: Final[str] = "https://api.olymptrade.com"

    def __init__(
        self,
        auth_token: Optional[str] = None,
        account_id: Optional[str] = None,
        use_simulated_mode: bool = True,
    ) -> None:
        """Initialize the Olymp Trade client.

        Args:
            auth_token: Session token or API authorization token.
            account_id: Demo account identifier.
            use_simulated_mode: If True, uses local simulation engine until
                credentials are provided.
        """
        self._auth_token: Optional[str] = auth_token
        self._account_id: Optional[str] = account_id
        self._use_simulated_mode: bool = use_simulated_mode
        self._is_connected: bool = False
        self._demo_balance: float = 10000.0
        self._session: requests.Session = requests.Session()

        if self._auth_token:
            self._session.headers.update({
                "Authorization": f"Bearer {self._auth_token}",
                "Content-Type": "application/json",
            })
            self._is_connected = True
            logger.info("OlympTradeClient configured with user authentication token.")
        else:
            logger.info("OlympTradeClient operating in local demo simulation mode.")

    @property
    def is_connected(self) -> bool:
        """Return connection status to Olymp Trade."""
        return self._is_connected

    @property
    def is_simulated(self) -> bool:
        """Return True if running in local simulation mode."""
        return self._use_simulated_mode

    def set_credentials(self, auth_token: str, account_id: Optional[str] = None) -> bool:
        """Update client credentials and connect to live Olymp Trade demo account.

        Args:
            auth_token: Olymp Trade user token / session token.
            account_id: Demo account ID.

        Returns:
            True if credentials configured successfully.
        """
        self._auth_token = auth_token
        self._account_id = account_id
        self._use_simulated_mode = False
        self._session.headers.update({
            "Authorization": f"Bearer {self._auth_token}",
            "Content-Type": "application/json",
        })
        self._is_connected = True
        logger.info("Updated Olymp Trade credentials. Switched to live demo execution mode.")
        return True

    def place_demo_trade(
        self,
        asset_symbol: str,
        direction: str,
        amount_usd: float,
        duration_seconds: int = 60,
    ) -> Dict:
        """Execute a Fixed Time Trade on the Olymp Trade demo account.

        Args:
            asset_symbol: Target asset (e.g., 'gold', 'XAUUSD').
            direction: Trade direction ('CALL' or 'PUT').
            amount_usd: Trade stake in USD.
            duration_seconds: Trade expiration duration (default: 60s for 1-minute).

        Returns:
            Dictionary containing trade execution details and order ID.
        """
        if self._use_simulated_mode or not self._auth_token:
            logger.info(
                "Executing simulated trade: %s $%.2f on %s for %ds",
                direction,
                amount_usd,
                asset_symbol,
                duration_seconds,
            )
            return {
                "status": "success",
                "mode": "simulated_demo",
                "order_id": f"sim_{int(time.time() * 1000)}",
                "asset": asset_symbol,
                "direction": direction,
                "amount": amount_usd,
                "duration": duration_seconds,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            }

        # Live Olymp Trade API execution endpoint
        try:
            endpoint_url = f"{self.DEFAULT_BASE_URL}/v1/ftt/orders"
            payload = {
                "account_id": self._account_id,
                "asset": asset_symbol.lower(),
                "dir": "up" if direction.upper() == "CALL" else "down",
                "amount": amount_usd,
                "duration": duration_seconds,
                "demo": True,
            }
            response = self._session.post(endpoint_url, json=payload, timeout=5)
            if response.status_code in (200, 201):
                logger.info("Olymp Trade order placed successfully: %s", response.text)
                return response.json()
            else:
                logger.error("Olymp Trade API error [%d]: %s", response.status_code, response.text)
                return {"status": "error", "code": response.status_code, "message": response.text}
        except Exception as exec_error:
            logger.exception("Failed to dispatch order to Olymp Trade: %s", exec_error)
            return {"status": "error", "message": str(exec_error)}

    def get_account_balance(self) -> float:
        """Retrieve current demo account balance."""
        if self._use_simulated_mode or not self._auth_token:
            return self._demo_balance

        try:
            url = f"{self.DEFAULT_BASE_URL}/v1/users/balance"
            res = self._session.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                self._demo_balance = float(data.get("demo_balance", self._demo_balance))
        except Exception as balance_err:
            logger.debug("Could not fetch Olymp Trade balance: %s", balance_err)

        return self._demo_balance
