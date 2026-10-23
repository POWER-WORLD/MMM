"""
Main Entry Point for the Gold Trading Analysis Platform.

Orchestrates all platform components:
- Real-time gold price fetching
- 10-second candle building
- 7 technical analysis agents
- Consensus-based trade execution
- Real-time web dashboard

Usage:
    python main.py
"""

import logging
import os
import sys
import signal
import time
import threading
from datetime import datetime, timedelta, timezone
from typing import Optional

import pandas as pd

from config import PLATFORM_CONFIG
from core.price_engine import GoldPriceEngine
from core.candle_builder import CandleBuilder, CandleData
from core.data_store import PlatformDataStore
from agents.base_agent import TradeDirection
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
from dashboard.app import create_dashboard_application
from dashboard.socket_events import DashboardEventEmitter


class GoldTradingPlatform:
    """
    Main platform orchestrator that coordinates all components.

    Manages the lifecycle of the price engine, candle builder,
    analysis agents, trade executor, and web dashboard.
    """

    def __init__(self) -> None:
        """Initialize all platform components."""
        self._setup_logging()
        self.logger = logging.getLogger("platform")
        self.logger.info("Initializing Gold Trading Analysis Platform...")

        PLATFORM_CONFIG.ensure_directories_exist()

        # Core components
        self.data_store = PlatformDataStore(
            max_candles=PLATFORM_CONFIG.price_engine.MAX_CANDLES_IN_MEMORY
        )

        self.candle_builder = CandleBuilder(
            candle_interval_seconds=PLATFORM_CONFIG.price_engine.CANDLE_INTERVAL_SECONDS,
            on_candle_complete_callback=self._on_candle_completed
        )

        self.price_engine = GoldPriceEngine(
            on_price_update_callback=self._on_price_update
        )

        # Analysis agents
        self.analysis_agents = self._initialize_analysis_agents()
        self.consensus_engine = ConsensusEngine(
            agents=self.analysis_agents,
            required_consensus_count=PLATFORM_CONFIG.agent.REQUIRED_CONSENSUS_COUNT
        )

        # Trading components
        self.trade_executor = TradeExecutor(
            initial_balance=PLATFORM_CONFIG.trading.INITIAL_DEMO_BALANCE_USD,
            payout_percentage=PLATFORM_CONFIG.trading.PAYOUT_PERCENTAGE
        )
        self.performance_tracker = PerformanceTracker(
            initial_balance=PLATFORM_CONFIG.trading.INITIAL_DEMO_BALANCE_USD
        )
        self.olymp_trade_client = OlympTradeClient(
            auth_token=PLATFORM_CONFIG.trading.OLYMP_TRADE_AUTH_TOKEN or None,
            account_id=PLATFORM_CONFIG.trading.OLYMP_TRADE_ACCOUNT_ID or None,
            use_simulated_mode=PLATFORM_CONFIG.trading.USE_OLYMP_TRADE_DEMO
        )

        # Platform state & dynamic runtime configuration
        self._is_running = False
        self._shutdown_event = threading.Event()
        self._analysis_lock = threading.Lock()
        self._last_trade_time: Optional[datetime] = None
        self._trade_settlement_timers: dict = {}
        self._last_consensus_data: Optional[dict] = None

        # User-configurable parameters (timeframe, fixed-time duration, stake)
        self.active_candle_interval_seconds: int = PLATFORM_CONFIG.price_engine.CANDLE_INTERVAL_SECONDS
        self.active_trade_duration_seconds: int = PLATFORM_CONFIG.trading.TRADE_DURATION_SECONDS
        self.active_trade_amount_usd: float = PLATFORM_CONFIG.trading.DEFAULT_TRADE_AMOUNT_USD

        # Dashboard components
        self.flask_application, self.socket_io = create_dashboard_application(
            get_state_callback=self._get_full_state_dict,
            get_config_callback=self._get_runtime_config,
            update_config_callback=self._update_runtime_config,
        )
        self.event_emitter = DashboardEventEmitter(socket_io=self.socket_io)

        # Register socket events
        self._register_socket_events()

        self.logger.info("Platform initialization complete. All components ready.")

    def _setup_logging(self) -> None:
        """Configure the logging system for the platform."""
        PLATFORM_CONFIG.ensure_directories_exist()
        logging.basicConfig(
            level=getattr(logging, PLATFORM_CONFIG.logging.LOG_LEVEL),
            format=PLATFORM_CONFIG.logging.LOG_FORMAT,
            datefmt=PLATFORM_CONFIG.logging.LOG_DATE_FORMAT,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(
                    os.path.join(PLATFORM_CONFIG.logging.LOG_DIRECTORY, "platform.log"),
                    encoding="utf-8"
                )
            ]
        )

    def _initialize_analysis_agents(self) -> list:
        """Create and return all 7 analysis agents."""
        agents = [
            RelativeStrengthIndexAgent(),
            MovingAverageConvergenceDivergenceAgent(),
            BollingerBandsAgent(),
            ExponentialMovingAverageCrossoverAgent(),
            StochasticOscillatorAgent(),
            AverageDirectionalIndexAgent(),
            IchimokuCloudAgent(),
        ]
        self.logger.info(
            "Initialized %d analysis agents: %s",
            len(agents),
            ", ".join(agent.agent_name for agent in agents)
        )
        return agents

    def _register_socket_events(self) -> None:
        """Register WebSocket event handlers for client connections."""
        @self.socket_io.on("connect")
        def handle_client_connect():
            self.logger.info("Dashboard client connected.")
            self._send_full_state_to_client()

        @self.socket_io.on("disconnect")
        def handle_client_disconnect():
            self.logger.info("Dashboard client disconnected.")

        @self.socket_io.on("request_full_state")
        def handle_full_state_request():
            self._send_full_state_to_client()

        @self.socket_io.on("update_config")
        def handle_update_config(data):
            self.logger.info("Received update_config socket event: %s", data)
            if isinstance(data, dict):
                self._update_runtime_config(data)

    def _get_runtime_config(self) -> dict:
        """Return the current dynamic platform runtime configuration."""
        return {
            "candle_interval_seconds": self.active_candle_interval_seconds,
            "trade_duration_seconds": self.active_trade_duration_seconds,
            "trade_amount_usd": self.active_trade_amount_usd,
            "payout_percentage": PLATFORM_CONFIG.trading.PAYOUT_PERCENTAGE,
            "asset_symbol": "XAU/USD (Spot Gold)",
            "olymp_trade_connected": self.olymp_trade_client.is_connected,
            "olymp_trade_simulated": self.olymp_trade_client.is_simulated,
            "olymp_trade_balance": self.olymp_trade_client.get_account_balance(),
        }

    def _update_runtime_config(self, updates: dict) -> dict:
        """
        Update the dynamic runtime platform configuration.

        Args:
            updates: Dictionary with updated configuration values.

        Returns:
            The complete updated runtime configuration dictionary.
        """
        if not isinstance(updates, dict):
            return self._get_runtime_config()

        if "candle_interval_seconds" in updates:
            try:
                new_interval = int(updates["candle_interval_seconds"])
                if new_interval in (5, 10, 15, 30, 60):
                    self.active_candle_interval_seconds = new_interval
                    self.candle_builder.set_interval(new_interval)
                    self.logger.info(
                        "Runtime candle interval updated to %d seconds.",
                        new_interval
                    )
            except (ValueError, TypeError) as conv_err:
                self.logger.warning("Invalid candle_interval_seconds value: %s", conv_err)

        if "trade_duration_seconds" in updates:
            try:
                new_duration = int(updates["trade_duration_seconds"])
                if new_duration in (60, 120, 180, 300):
                    self.active_trade_duration_seconds = new_duration
                    self.logger.info(
                        "Runtime trade duration updated to %d seconds.",
                        new_duration
                    )
            except (ValueError, TypeError) as conv_err:
                self.logger.warning("Invalid trade_duration_seconds value: %s", conv_err)

        if "trade_amount_usd" in updates:
            try:
                new_amount = float(updates["trade_amount_usd"])
                if new_amount > 0:
                    self.active_trade_amount_usd = new_amount
                    self.logger.info(
                        "Runtime trade stake updated to $%.2f.",
                        new_amount
                    )
            except (ValueError, TypeError) as conv_err:
                self.logger.warning("Invalid trade_amount_usd value: %s", conv_err)

        if "olymp_auth_token" in updates:
            token = str(updates["olymp_auth_token"]).strip()
            account_id = updates.get("olymp_account_id")
            if account_id:
                account_id = str(account_id).strip()
            if token:
                self.olymp_trade_client.set_credentials(auth_token=token, account_id=account_id)
                self.logger.info("Olymp Trade credentials configured successfully.")

        updated_config = self._get_runtime_config()
        try:
            self.socket_io.emit("config_update", updated_config)
        except Exception as emit_err:
            self.logger.debug("Notice on config_update emit: %s", emit_err)

        return updated_config

    def _get_full_state_dict(self) -> dict:
        """Construct the complete platform state dictionary."""
        current_price, price_timestamp = self.data_store.get_current_price()
        candles_dataframe = self.data_store.get_candles_dataframe()

        candles_list = []
        if candles_dataframe is not None and not candles_dataframe.empty:
            for _, row in candles_dataframe.iterrows():
                ts = row["timestamp"]
                try:
                    epoch_seconds = int(ts.timestamp()) if hasattr(ts, "timestamp") else int(pd.to_datetime(ts).timestamp())
                except Exception:
                    epoch_seconds = int(time.time())
                candles_list.append({
                    "time": epoch_seconds,
                    "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                })

        return {
            "current_price": current_price,
            "price_timestamp": price_timestamp.isoformat() if price_timestamp else None,
            "candles": candles_list,
            "config": self._get_runtime_config(),
            "agent_signals": self.data_store.get_agent_signals(),
            "consensus": self._last_consensus_data,
            "agent_statistics": self.consensus_engine.get_all_agent_statistics(),
            "performance": self.performance_tracker.get_overall_statistics(),
            "recent_trades": self.performance_tracker.get_recent_trades(count=50),
            "active_trade": self._get_active_trade_info(),
            "current_balance": self.trade_executor.current_balance,
            "olymp_trade": {
                "is_connected": self.olymp_trade_client.is_connected,
                "is_simulated": self.olymp_trade_client.is_simulated,
                "demo_balance": self.olymp_trade_client.get_account_balance(),
            },
        }

    def _send_full_state_to_client(self) -> None:
        """Send the complete current platform state to a connecting client."""
        full_state = self._get_full_state_dict()
        self.event_emitter.emit_full_state(full_state)

    def _on_price_update(self, timestamp: datetime, price: float) -> None:
        """
        Callback invoked when a new price tick is received from the price engine.

        Args:
            timestamp: The timestamp of the price tick.
            price: The current gold price.
        """
        self.data_store.set_current_price(price=price, timestamp=timestamp)
        self.candle_builder.add_tick(timestamp=timestamp, price=price)

        self.event_emitter.emit_price_update(
            price=price,
            timestamp=timestamp.isoformat()
        )

    def _on_candle_completed(self, candle_data: CandleData) -> None:
        """
        Callback invoked when a 10-second candle is finalized.

        Args:
            candle_data: The completed candle data.
        """
        ts = candle_data.timestamp
        try:
            epoch_seconds = int(ts.timestamp()) if hasattr(ts, "timestamp") else int(pd.to_datetime(ts).timestamp())
        except Exception:
            epoch_seconds = int(time.time())

        candle_dict = {
            "time": epoch_seconds,
            "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
            "open": candle_data.open_price,
            "high": candle_data.high_price,
            "low": candle_data.low_price,
            "close": candle_data.close_price,
            "volume": candle_data.volume,
            "tick_count": candle_data.tick_count,
        }
        self.data_store.add_candle(candle_data=candle_dict)

        self.event_emitter.emit_candle_update(candle=candle_dict)

        # Run analysis in a separate thread to avoid blocking
        analysis_thread = threading.Thread(
            target=self._run_analysis_cycle,
            name="analysis-cycle",
            daemon=True
        )
        analysis_thread.start()

    def _run_analysis_cycle(self) -> None:
        """
        Execute one full analysis cycle: collect agent signals, check consensus, and optionally place a trade.
        """
        if not self._analysis_lock.acquire(blocking=False):
            return

        try:
            candles_dataframe = self.data_store.get_candles_dataframe()
            if candles_dataframe is None or len(candles_dataframe) < PLATFORM_CONFIG.agent.MINIMUM_CANDLES_FOR_ANALYSIS:
                self.logger.debug(
                    "Insufficient candle data for analysis. Have %d, need %d.",
                    len(candles_dataframe) if candles_dataframe is not None else 0,
                    PLATFORM_CONFIG.agent.MINIMUM_CANDLES_FOR_ANALYSIS
                )
                return

            # Get historical data for context
            historical_dataframe = self.price_engine.get_historical_data()

            # Run consensus evaluation
            consensus_result = self.consensus_engine.evaluate_market(
                candles_dataframe=candles_dataframe,
                historical_dataframe=historical_dataframe
            )

            # Build agent lookup to attach success rates
            agent_lookup = {agent.agent_name: agent for agent in self.analysis_agents}

            # Prepare signal data for dashboard
            signals_for_dashboard = []
            for trade_signal in consensus_result.signals:
                agent_instance = agent_lookup.get(trade_signal.agent_name)
                success_rate_val = (agent_instance.get_success_rate() / 100.0) if agent_instance else 0.0
                signals_for_dashboard.append({
                    "agent_name": trade_signal.agent_name,
                    "direction": trade_signal.direction.value,
                    "confidence": trade_signal.confidence,
                    "reasoning": trade_signal.reasoning,
                    "indicator_values": trade_signal.indicator_values,
                    "success_rate": success_rate_val,
                })

            self.data_store.set_agent_signals(signals=signals_for_dashboard)
            self.event_emitter.emit_agent_signals(signals=signals_for_dashboard)

            # Prepare consensus data for dashboard
            consensus_data = {
                "consensus_reached": consensus_result.consensus_reached,
                "direction": consensus_result.direction.value if consensus_result.direction else None,
                "average_confidence": consensus_result.average_confidence,
                "agreeing_agent_count": consensus_result.agreeing_agent_count,
                "total_agents": len(self.analysis_agents),
                "timestamp": consensus_result.timestamp.isoformat(),
            }
            self._last_consensus_data = consensus_data
            self.event_emitter.emit_consensus_result(consensus=consensus_data)

            # Check if we should place a trade
            if consensus_result.consensus_reached and consensus_result.direction:
                self._attempt_trade_placement(
                    direction=consensus_result.direction,
                    signals=consensus_result.signals,
                    average_confidence=consensus_result.average_confidence
                )

            # Emit updated performance
            self.event_emitter.emit_performance_update(
                performance=self.performance_tracker.get_overall_statistics()
            )

        except Exception as analysis_error:
            self.logger.error("Analysis cycle failed: %s", analysis_error, exc_info=True)
        finally:
            self._analysis_lock.release()

    def _attempt_trade_placement(
        self,
        direction: TradeDirection,
        signals: list,
        average_confidence: float
    ) -> None:
        """
        Attempt to place a trade if all conditions are met.

        Args:
            direction: The consensus trade direction.
            signals: List of trade signals from all agents.
            average_confidence: Average confidence across agreeing agents.
        """
        # Check if there's already a pending trade
        if self.trade_executor.has_pending_trade():
            self.logger.debug("Trade placement skipped: pending trade exists.")
            return

        # Check cooldown period
        if self._last_trade_time is not None:
            cooldown_elapsed = (datetime.now() - self._last_trade_time).total_seconds()
            if cooldown_elapsed < PLATFORM_CONFIG.trading.COOLDOWN_BETWEEN_TRADES_SECONDS:
                self.logger.debug(
                    "Trade placement skipped: cooldown period. %d seconds remaining.",
                    PLATFORM_CONFIG.trading.COOLDOWN_BETWEEN_TRADES_SECONDS - cooldown_elapsed
                )
                return

        # Check minimum confidence
        if average_confidence < PLATFORM_CONFIG.agent.MINIMUM_CONFIDENCE_THRESHOLD:
            self.logger.debug(
                "Trade placement skipped: confidence %.2f below threshold %.2f.",
                average_confidence,
                PLATFORM_CONFIG.agent.MINIMUM_CONFIDENCE_THRESHOLD
            )
            return

        # Get current price for entry
        current_price = self.data_store.get_latest_price()
        if current_price is None:
            self.logger.warning("Trade placement skipped: no current price available.")
            return

        # Place the trade using dynamic user-configured stake and contract duration
        trade_record = self.trade_executor.place_trade(
            direction=direction,
            entry_price=current_price,
            amount=self.active_trade_amount_usd,
            agent_signals=signals,
            duration_seconds=self.active_trade_duration_seconds
        )

        self._last_trade_time = datetime.now()

        # Place demo trade on Olymp Trade (runs in simulated mode or live demo endpoint)
        try:
            olymp_order = self.olymp_trade_client.place_demo_trade(
                asset_symbol=PLATFORM_CONFIG.trading.OLYMP_TRADE_ASSET,
                direction=direction.value,
                amount_usd=self.active_trade_amount_usd,
                duration_seconds=self.active_trade_duration_seconds,
            )
            self.logger.info(
                "Olymp Trade Demo Execution: status=%s | order_id=%s | mode=%s",
                olymp_order.get("status"),
                olymp_order.get("order_id"),
                olymp_order.get("mode", "live_demo"),
            )
        except Exception as ot_err:
            self.logger.warning("Olymp Trade demo order dispatch notice: %s", ot_err)

        self.logger.info(
            "TRADE PLACED: %s at %.2f | Stake: $%.2f | Duration: %ds | Confidence: %.1f%%",
            direction.value,
            current_price,
            self.active_trade_amount_usd,
            self.active_trade_duration_seconds,
            average_confidence * 100
        )

        # Emit trade update to dashboard
        trade_info = self._format_trade_for_dashboard(trade_record)
        self.event_emitter.emit_trade_update(trade=trade_info)

        # Schedule trade settlement according to dynamic trade duration
        settlement_timer = threading.Timer(
            interval=self.active_trade_duration_seconds,
            function=self._settle_trade,
            args=[trade_record]
        )
        settlement_timer.daemon = True
        settlement_timer.start()
        self._trade_settlement_timers[trade_record.trade_id] = settlement_timer

    def _settle_trade(self, trade_record) -> None:
        """
        Settle a trade after its duration has elapsed.

        Args:
            trade_record: The trade record to settle.
        """
        try:
            exit_price = self.data_store.get_latest_price()
            if exit_price is None:
                self.logger.warning(
                    "Cannot settle trade %s: no exit price available.",
                    trade_record.trade_id
                )
                return

            settled_trade = self.trade_executor.settle_trade(
                trade_record=trade_record,
                exit_price=exit_price
            )

            # Record in performance tracker
            self.performance_tracker.record_trade(trade_record=settled_trade)

            # Update agent statistics
            was_correct = settled_trade.result == "WIN"
            trade_direction = (
                TradeDirection.CALL if settled_trade.direction == "CALL"
                else TradeDirection.PUT
            )
            self.consensus_engine.record_trade_result(
                direction=trade_direction,
                was_correct=was_correct
            )

            self.logger.info(
                "TRADE SETTLED: %s | Entry: %.2f → Exit: %.2f | Result: %s | P&L: $%.2f",
                settled_trade.direction,
                settled_trade.entry_price,
                settled_trade.exit_price,
                settled_trade.result,
                settled_trade.profit_loss
            )

            # Emit updates to dashboard
            trade_info = self._format_trade_for_dashboard(settled_trade)
            self.event_emitter.emit_trade_update(trade=trade_info)
            self.event_emitter.emit_performance_update(
                performance=self.performance_tracker.get_overall_statistics()
            )

            # Clean up timer reference
            self._trade_settlement_timers.pop(trade_record.trade_id, None)

        except Exception as settlement_error:
            self.logger.error(
                "Trade settlement failed for %s: %s",
                trade_record.trade_id,
                settlement_error,
                exc_info=True
            )

    def _get_active_trade_info(self) -> Optional[dict]:
        """Get information about the currently active trade, if any."""
        if not self.trade_executor.has_pending_trade():
            return None
        pending_trade = self.trade_executor.get_pending_trade()
        if pending_trade is None:
            return None
        return self._format_trade_for_dashboard(pending_trade)

    def _format_trade_for_dashboard(self, trade_record) -> dict:
        """
        Format a trade record for transmission to the dashboard.

        Args:
            trade_record: The trade record to format.

        Returns:
            Dictionary with formatted trade information.
        """
        return {
            "trade_id": trade_record.trade_id,
            "direction": trade_record.direction,
            "entry_price": trade_record.entry_price,
            "entry_time": trade_record.entry_time.isoformat(),
            "exit_price": trade_record.exit_price,
            "exit_time": trade_record.exit_time.isoformat() if trade_record.exit_time else None,
            "duration_seconds": trade_record.duration_seconds,
            "amount": trade_record.amount,
            "result": trade_record.result,
            "profit_loss": trade_record.profit_loss,
            "payout_percentage": trade_record.payout_percentage,
        }

    def run_analysis_cycle(self) -> None:
        """Execute one full analysis cycle synchronously (public entry point for testing)."""
        self._run_analysis_cycle()

    def settle_active_trade(self, exit_price: Optional[float] = None) -> Optional[dict]:
        """
        Settle currently active pending trade immediately with given or latest price.

        Useful for deterministic testing and manual settlement.

        Args:
            exit_price: Optional exit price to settle at (defaults to latest spot price).

        Returns:
            Dictionary with formatted settled trade info, or None if no active trade.
        """
        if not self.trade_executor.has_pending_trade():
            return None
        pending = self.trade_executor.get_pending_trade()
        if pending is None:
            return None

        # Cancel active settlement timer
        timer = self._trade_settlement_timers.pop(pending.trade_id, None)
        if timer is not None:
            timer.cancel()

        settle_px = exit_price if exit_price is not None else self.data_store.get_latest_price()
        if settle_px is None:
            settle_px = pending.entry_price

        settled_trade = self.trade_executor.settle_trade(
            trade_record=pending,
            exit_price=settle_px
        )

        self.performance_tracker.record_trade(trade_record=settled_trade)

        was_correct = settled_trade.result == "WIN"
        trade_direction = (
            TradeDirection.CALL if settled_trade.direction == "CALL"
            else TradeDirection.PUT
        )
        self.consensus_engine.record_trade_result(
            direction=trade_direction,
            was_correct=was_correct
        )

        trade_info = self._format_trade_for_dashboard(settled_trade)
        self.event_emitter.emit_trade_update(trade=trade_info)
        self.event_emitter.emit_performance_update(
            performance=self.performance_tracker.get_overall_statistics()
        )
        return trade_info

    def load_candles_dataframe(self, candles_dataframe: pd.DataFrame) -> None:
        """
        Load an arbitrary DataFrame of candles directly into the platform data store.

        Args:
            candles_dataframe: DataFrame containing timestamp, open, high, low, close, volume.
        """
        for _, row in candles_dataframe.iterrows():
            ts = row["timestamp"] if "timestamp" in row else row.name
            try:
                epoch_seconds = int(ts.timestamp()) if hasattr(ts, "timestamp") else int(pd.to_datetime(ts).timestamp())
            except Exception:
                epoch_seconds = int(time.time())

            candle_dict = {
                "time": epoch_seconds,
                "timestamp": ts,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row.get("volume", 0)),
                "tick_count": int(row.get("tick_count", 1)),
            }
            self.data_store.add_candle(candle_data=candle_dict)

        if not candles_dataframe.empty:
            last_price = float(candles_dataframe.iloc[-1]["close"])
            self.data_store.set_current_price(
                price=last_price,
                timestamp=datetime.now(tz=timezone.utc)
            )

    def start(self) -> None:
        """
        Start the Gold Trading Analysis Platform.

        Launches the price engine, loads historical data, and starts the web dashboard.
        """
        self.logger.info("=" * 70)
        self.logger.info("  GOLD TRADING ANALYSIS PLATFORM - STARTING")
        self.logger.info("=" * 70)
        self.logger.info("  Gold Ticker: %s", PLATFORM_CONFIG.price_engine.GOLD_TICKER_SYMBOL)
        self.logger.info("  Candle Interval: %d seconds", PLATFORM_CONFIG.price_engine.CANDLE_INTERVAL_SECONDS)
        self.logger.info("  Trade Duration: %d seconds", PLATFORM_CONFIG.trading.TRADE_DURATION_SECONDS)
        self.logger.info("  Initial Balance: $%.2f", PLATFORM_CONFIG.trading.INITIAL_DEMO_BALANCE_USD)
        self.logger.info("  Analysis Agents: %d", len(self.analysis_agents))
        self.logger.info("  Consensus Required: %d/%d agents", PLATFORM_CONFIG.agent.REQUIRED_CONSENSUS_COUNT, len(self.analysis_agents))
        self.logger.info("  Dashboard: http://%s:%d", PLATFORM_CONFIG.dashboard.HOST, PLATFORM_CONFIG.dashboard.PORT)
        self.logger.info("=" * 70)

        self._is_running = True

        # Load historical data first
        self.logger.info("Loading historical gold price data...")
        self._load_historical_candles()

        # Run initial analysis cycle on historical candles
        self.logger.info("Running initial multi-agent analysis cycle...")
        self._run_analysis_cycle()

        # Start price engine
        self.logger.info("Starting real-time price engine...")
        self.price_engine.start()

        # Start the Flask-SocketIO server (this blocks)
        self.logger.info("Starting dashboard server...")
        self.logger.info(
            "Dashboard available at: http://%s:%d",
            PLATFORM_CONFIG.dashboard.HOST,
            PLATFORM_CONFIG.dashboard.PORT
        )

        try:
            self.socket_io.run(
                self.flask_application,
                host=PLATFORM_CONFIG.dashboard.HOST,
                port=PLATFORM_CONFIG.dashboard.PORT,
                debug=PLATFORM_CONFIG.dashboard.DEBUG_MODE,
                allow_unsafe_werkzeug=True,
                use_reloader=False,
                log_output=False
            )
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received.")
        finally:
            self.stop()

    def _load_historical_candles(self) -> None:
        """
        Load historical price data and convert to 10-second candles for initial analysis.
        """
        try:
            historical_dataframe = self.price_engine.get_historical_data()
            if historical_dataframe is None or historical_dataframe.empty:
                self.logger.warning("No historical data available. Starting with empty candle buffer.")
                return

            self.logger.info(
                "Loaded %d historical data points. Converting to 10-second candles...",
                len(historical_dataframe)
            )

            # Use historical 1-minute data as candles directly for initial analysis
            # Each 1-minute bar represents data that agents can analyze
            for _, row in historical_dataframe.tail(200).iterrows():
                ts = row["timestamp"] if "timestamp" in row else row.name
                try:
                    epoch_seconds = int(ts.timestamp()) if hasattr(ts, "timestamp") else int(pd.to_datetime(ts).timestamp())
                except Exception:
                    epoch_seconds = int(time.time())

                close_val = float(row["close"]) if "close" in row else float(row["Close"])
                candle_dict = {
                    "time": epoch_seconds,
                    "timestamp": ts,
                    "open": float(row["open"]) if "open" in row else float(row["Open"]),
                    "high": float(row["high"]) if "high" in row else float(row["High"]),
                    "low": float(row["low"]) if "low" in row else float(row["Low"]),
                    "close": close_val,
                    "volume": int(row.get("volume", row.get("Volume", 0))),
                    "tick_count": 1,
                }
                self.data_store.add_candle(candle_data=candle_dict)

            # Set initial price from latest candle
            if not historical_dataframe.empty:
                last_row = historical_dataframe.iloc[-1]
                last_price = float(last_row["close"]) if "close" in last_row else float(last_row["Close"])
                self.data_store.set_current_price(price=last_price, timestamp=datetime.now(tz=timezone.utc))

            self.logger.info(
                "Loaded %d historical candles into data store.",
                self.data_store.get_candle_count()
            )

        except Exception as load_error:
            self.logger.error("Failed to load historical data: %s", load_error, exc_info=True)

    def stop(self) -> None:
        """Gracefully shut down all platform components."""
        if not self._is_running:
            return

        self.logger.info("Shutting down Gold Trading Analysis Platform...")
        self._is_running = False
        self._shutdown_event.set()

        # Cancel all pending settlement timers
        for trade_id, timer in self._trade_settlement_timers.items():
            timer.cancel()
            self.logger.debug("Cancelled settlement timer for trade %s", trade_id)
        self._trade_settlement_timers.clear()

        # Stop price engine
        self.price_engine.stop()

        # Print final statistics
        self._print_final_statistics()

        self.logger.info("Platform shutdown complete.")

    def _print_final_statistics(self) -> None:
        """Print comprehensive final statistics to the console."""
        stats = self.performance_tracker.get_overall_statistics()
        agent_stats = self.consensus_engine.get_all_agent_statistics()

        self.logger.info("=" * 70)
        self.logger.info("  FINAL SESSION STATISTICS")
        self.logger.info("=" * 70)
        self.logger.info("  Total Trades: %d", stats["total_trades"])
        self.logger.info("  Winning Trades: %d", stats["winning_trades"])
        self.logger.info("  Losing Trades: %d", stats["losing_trades"])
        self.logger.info("  Overall Success Rate: %.2f%%", stats["success_rate"])
        self.logger.info("  Total P&L: $%.2f", stats["total_profit_loss"])
        self.logger.info("  Final Balance: $%.2f", stats["current_balance"])
        self.logger.info("  Return: %.2f%%", stats["return_percentage"])
        self.logger.info("-" * 70)
        self.logger.info("  AGENT PERFORMANCE:")
        for agent_stat in agent_stats:
            self.logger.info(
                "    %-40s | Predictions: %3d | Success: %6.2f%%",
                agent_stat["agent_name"],
                agent_stat["total_predictions"],
                agent_stat["success_rate"]
            )
        self.logger.info("=" * 70)


def main() -> None:
    """Main entry point for the Gold Trading Analysis Platform."""
    platform = GoldTradingPlatform()

    # Handle SIGINT for graceful shutdown
    def signal_handler(signal_number, frame):
        platform.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    platform.start()


if __name__ == "__main__":
    main()
