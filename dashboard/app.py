"""
Flask Dashboard Application Module for Gold Trading Analysis Platform.

This module creates and configures the Flask web application with
Flask-SocketIO integration and comprehensive REST API endpoints
for real-time dashboard functionality.
"""

import os
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_socketio import SocketIO

from config import PLATFORM_CONFIG


def create_dashboard_application(
    get_state_callback: Optional[Callable[[], Dict[str, Any]]] = None,
    get_config_callback: Optional[Callable[[], Dict[str, Any]]] = None,
    update_config_callback: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
) -> Tuple[Flask, SocketIO]:
    """Create and configure the Flask dashboard application.

    Args:
        get_state_callback: Callback that returns the latest platform state.
        get_config_callback: Callback that returns runtime configuration.
        update_config_callback: Callback to update runtime configuration.

    Returns:
        A tuple of (Flask application, SocketIO instance).
    """
    react_dist_folder = os.path.join(os.path.dirname(__file__), "static", "dist")

    application = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )
    application.config["SECRET_KEY"] = PLATFORM_CONFIG.dashboard.SECRET_KEY

    @application.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        return response

    socket_io = SocketIO(
        application,
        async_mode="threading",
        cors_allowed_origins="*",
    )

    @application.route("/")
    def index():
        """Serve the dashboard page."""
        react_index_path = os.path.join(react_dist_folder, "index.html")
        if os.path.exists(react_index_path):
            return send_from_directory(react_dist_folder, "index.html")
        return render_template("index.html")

    @application.route("/<path:filename>")
    def serve_static_dist(filename):
        """Serve React static assets from static/dist if present."""
        if os.path.exists(os.path.join(react_dist_folder, filename)):
            return send_from_directory(react_dist_folder, filename)
        return send_from_directory(application.static_folder, filename)

    @application.route("/api/status")
    def api_status():
        """Return platform operational status."""
        return jsonify({
            "status": "running",
            "server_time": datetime.now().isoformat(),
            "websocket_active": True,
        })

    @application.route("/api/config", methods=["GET", "POST"])
    def api_config():
        """Get or update runtime platform configuration."""
        if request.method == "POST":
            updates = request.get_json(silent=True) or {}
            if update_config_callback is not None:
                new_cfg = update_config_callback(updates)
                return jsonify({"status": "success", "config": new_cfg})
            return jsonify({"status": "error", "message": "Config updater not available"}), 400

        # GET
        if get_config_callback is not None:
            return jsonify(get_config_callback())
        return jsonify({
            "candle_interval_seconds": 10,
            "trade_duration_seconds": 60,
            "trade_amount_usd": 1.0,
            "payout_percentage": 0.82,
        })

    @application.route("/api/state")
    def api_state():
        """Return full platform state snapshot."""
        if get_state_callback is not None:
            state = get_state_callback()
            return jsonify(state)
        return jsonify({"error": "State provider not configured", "status": "running"})

    @application.route("/api/price")
    def api_price():
        """Return current spot price."""
        if get_state_callback is not None:
            state = get_state_callback()
            return jsonify({
                "price": state.get("current_price"),
                "timestamp": state.get("price_timestamp"),
            })
        return jsonify({"price": None})

    @application.route("/api/candles")
    def api_candles():
        """Return current candle buffer."""
        if get_state_callback is not None:
            state = get_state_callback()
            return jsonify(state.get("candles", []))
        return jsonify([])

    @application.route("/api/signals")
    def api_signals():
        """Return analysis agent signals and consensus."""
        if get_state_callback is not None:
            state = get_state_callback()
            return jsonify({
                "agent_signals": state.get("agent_signals", []),
                "consensus": state.get("consensus", {}),
                "agent_statistics": state.get("agent_statistics", []),
            })
        return jsonify({"agent_signals": [], "consensus": {}})

    @application.route("/api/performance")
    def api_performance():
        """Return performance statistics."""
        if get_state_callback is not None:
            state = get_state_callback()
            return jsonify(state.get("performance", {}))
        return jsonify({})

    @application.route("/api/trades")
    def api_trades():
        """Return active trade and trade history."""
        if get_state_callback is not None:
            state = get_state_callback()
            return jsonify({
                "active_trade": state.get("active_trade"),
                "recent_trades": state.get("recent_trades", []),
            })
        return jsonify({"active_trade": None, "recent_trades": []})

    return application, socket_io
