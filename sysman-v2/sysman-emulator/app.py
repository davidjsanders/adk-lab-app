"""SysMan Multi-System Emulator Flask Application.

Emulates Linux, Jira, and Confluence system health, resource metrics,
syslog details, and control commands, loading custom system definitions
from a Secret Manager mounted JSON configuration file.
"""

import json
import logging
import logging_config
import os
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union
from dotenv import load_dotenv

from classes import ConfigDrivenSystemState
from helpers import register_secrets_to_secret_manager
from flask import Flask, jsonify, render_template, request, Response

load_dotenv()

app = Flask(__name__)

# Configure basic console logging
logging_config.setup_logging()
logger = logging.getLogger("sysman-emulator")

# Config path for Secret Manager mounted volume
SYSTEMS_CONFIG_PATH = os.getenv("SYSTEMS_CONFIG_PATH", "")
CONTROL_HEADER = os.getenv("CONTROL_HEADER", "X-Control-Password")
CONTROL_PASSWORD = str(uuid.uuid4())





# --- System Discovery and Initialization ---
SYSTEM_REGISTRY: Dict[str, ConfigDrivenSystemState] = {}
EMULATOR_CONFIG_PATH = os.getenv("EMULATOR_CONFIG_PATH", "").strip()

# Map of system ID to dynamic control password
CONTROL_PASSWORDS: Dict[str, str] = {}





def load_topology() -> None:
    """Discovers and parses host definitions from EMULATOR_CONFIG_PATH, environment variables, or defaults."""
    global SYSTEM_REGISTRY
    SYSTEM_REGISTRY.clear()

    # Priority 1: Load from EMULATOR_CONFIG_PATH if set
    if EMULATOR_CONFIG_PATH and os.path.exists(EMULATOR_CONFIG_PATH):
        try:
            with open(EMULATOR_CONFIG_PATH, "r", encoding="utf-8") as f:
                config = json.load(f)
            sys_id = config["system_id"]
            SYSTEM_REGISTRY[sys_id] = ConfigDrivenSystemState(config)
            logger.info(f"Loaded dynamic config-driven emulator for system: {sys_id} from {EMULATOR_CONFIG_PATH}")
            return
        except Exception as err:
            logger.error(f"Failed loading EMULATOR_CONFIG_PATH at '{EMULATOR_CONFIG_PATH}': {err}")

    # Priority 2: Fallback to SYSTEMS_CONFIG_PATH or default topology lists
    config_data: List[Dict[str, str]] = []
    if SYSTEMS_CONFIG_PATH and os.path.exists(SYSTEMS_CONFIG_PATH):
        try:
            with open(SYSTEMS_CONFIG_PATH, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            logger.info(f"Loaded system configurations dynamically from Secret Manager mounted config: {SYSTEMS_CONFIG_PATH}")
        except Exception as err:
            logger.error(f"Failed parsing SYSTEMS_CONFIG_PATH at '{SYSTEMS_CONFIG_PATH}': {err}")

    if not config_data:
        # Defaults
        logger.info("SYSTEMS_CONFIG_PATH missing or empty. Initializing default system topology.")
        config_data = [
            {"id": "linux-server-01", "type": "linux", "name": "Linux Core Host"},
            {"id": "jira-app-01", "type": "jira", "name": "Jira System Host"},
            {"id": "confluence-app-01", "type": "confluence", "name": "Confluence System Host"}
        ]

    for item in config_data:
        sys_id = item.get("id", "")
        sys_type = item.get("type", "").lower()
        sys_name = item.get("name", sys_id)

        if not sys_id or not sys_type:
            continue

        # Load matched spec configuration from config/ directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        specific_path = os.path.join(script_dir, "config", f"{sys_type}_config.json")
        
        config = None
        if os.path.exists(specific_path):
            try:
                with open(specific_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    config["system_id"] = sys_id
                    config["name"] = sys_name
            except Exception as err:
                logger.error(f"Failed reading specific config file {specific_path}: {err}")

        if not config:
            config = {
                "system_id": sys_id,
                "type": sys_type,
                "name": sys_name,
                "status": "HEALTHY",
                "metrics": [],
                "actions": []
            }

        SYSTEM_REGISTRY[sys_id] = ConfigDrivenSystemState(config)


# Perform initialization at module import time
load_topology()
CONTROL_PASSWORDS = register_secrets_to_secret_manager(
    list(SYSTEM_REGISTRY.keys()),
    CONTROL_PASSWORD,
    CONTROL_HEADER
)


@app.before_request
def touch_activities() -> None:
    """Checks and updates metrics calculations on target queries."""
    pass


@app.after_request
def add_security_headers(response: Response) -> Response:
    """Hardens security headers for production/Cloud Run compliance.

    Args:
        response: HTTP Response.

    Returns:
        Secure Response.
    """
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline'; "
        "frame-ancestors *;"
    )
    return response


@app.route("/")
def index() -> str:
    """Renders the HTML console interface showing live systems state.

    Returns:
        String containing page template html.
    """
    systems_summary = [sys.to_dict() for sys in SYSTEM_REGISTRY.values()]
    return render_template(
        "index.html",
        systems=systems_summary,
        control_header=CONTROL_HEADER
    )


@app.route("/api/status", methods=["GET"])
def get_status() -> Response:
    """Fetches real-time telemetry state for all registered systems.

    Query Parameters:
        system_id: Target system ID string.

    Returns:
        JSON Response list or dict.
    """
    sys_id = request.args.get("system_id", "")
    if sys_id:
        if sys_id in SYSTEM_REGISTRY:
            return jsonify(SYSTEM_REGISTRY[sys_id].to_dict())
        return jsonify({"error": "Not Found", "message": f"System '{sys_id}' not found"}), 404

    return jsonify({
        "status": "SUCCESS",
        "systems": [sys.to_dict() for sys in SYSTEM_REGISTRY.values()]
    })


@app.route("/api/logs", methods=["GET"])
def get_logs() -> Response:
    """Fetches diagnostic syslog streams.

    Query Parameters:
        system_id: Target system ID.
        limit: Max lines to return.

    Returns:
        JSON Response payload.
    """
    sys_id = request.args.get("system_id", "")
    limit_str = request.args.get("limit", "25")

    limit = 25
    if limit_str.isdigit():
        limit = int(limit_str)

    if not sys_id:
        return jsonify({"error": "Bad Request", "message": "Missing 'system_id' parameter"}), 400

    if sys_id not in SYSTEM_REGISTRY:
        return jsonify({"error": "Not Found", "message": f"System '{sys_id}' not found"}), 404

    target_sys = SYSTEM_REGISTRY[sys_id]
    target_sys.update_metrics()
    return jsonify({
        "status": "SUCCESS",
        "system_id": sys_id,
        "count": len(target_sys.logs[-limit:]),
        "logs": target_sys.logs[-limit:]
    })


@app.route("/metrics", methods=["GET"])
def prometheus_metrics() -> Response:
    """Exposes native Prometheus metrics for scrape ingestion.

    Returns:
        Plaintext Response in Prometheus format.
    """
    lines: List[str] = []
    for sys in SYSTEM_REGISTRY.values():
        sys.update_metrics()
        s_id = sys.system_id
        s_type = sys.system_type

        # Generate standard uptime and health prometheus lines
        lines.append(f'# HELP sysman_uptime_seconds Uptime of the system {s_id}')
        lines.append(f'# TYPE sysman_uptime_seconds gauge')
        lines.append(f'sysman_uptime_seconds{{system_id="{s_id}",type="{s_type}"}} {sys.uptime_seconds}')

        health_val = 1 if sys.status == "HEALTHY" else (2 if sys.status == "DEGRADED" else 0)
        lines.append(f'# HELP sysman_health_status Health of the system {s_id} (1=healthy, 2=degraded, 0=unhealthy)')
        lines.append(f'# TYPE sysman_health_status gauge')
        lines.append(f'sysman_health_status{{system_id="{s_id}",type="{s_type}"}} {health_val}')

        # Generic scraper for config-driven metrics
        for m in sys.metrics:
            m_id = m["id"].replace("-", "_")
            val = m.get("value")
            if isinstance(val, (int, float)):
                lines.append(f'sysman_{m_id}{{system_id="{s_id}"}} {val:.2f}')

    return Response("\n".join(lines) + "\n", mimetype="text/plain")


@app.route("/api/command", methods=["POST"])
def execute_command() -> Union[Response, Tuple[Response, int]]:
    """Receives and dispatches control commands on a specified system.

    Returns:
        JSON execution status.
    """
    payload = request.get_json(silent=True) or {}
    sys_id = payload.get("system_id", "").strip()
    command = payload.get("command", "").strip()
    params = payload.get("parameters", {})

    expected_pass = CONTROL_PASSWORDS.get(sys_id, CONTROL_PASSWORD)
    req_auth = request.headers.get(CONTROL_HEADER, "")
    if not req_auth or req_auth != expected_pass:
        logger.warning(f"Unauthorized command execution attempt on '{sys_id}' from {request.remote_addr}")
        return jsonify({"error": "Unauthorized", "message": "Invalid or missing auth header"}), 401

    if not sys_id or not command:
        return jsonify({"error": "Bad Request", "message": "Missing 'system_id' or 'command' parameters"}), 400

    if sys_id not in SYSTEM_REGISTRY:
        return jsonify({"error": "Not Found", "message": f"System '{sys_id}' not found"}), 404

    target_sys = SYSTEM_REGISTRY[sys_id]
    target_sys.update_metrics()
    res, status_code = target_sys.execute_command(command, params)
    return jsonify(res), status_code


@app.route("/health", methods=["GET"])
def health_check() -> Tuple[Response, int]:
    """Provides a container health check.

    Returns:
        Container healthy message.
    """
    return jsonify({"status": "healthy", "service": "sysman-emulator"}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8081"))
    debug_mode = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
