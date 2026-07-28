"""SysMan Multi-System Emulator Flask Application.

Emulates Linux, Jira, and Confluence system health, resource metrics,
syslog details, and control commands, loading custom system definitions
from a Secret Manager mounted JSON configuration file.
"""

from datetime import datetime, timezone
import json
import logging
import os
import random
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, Response

load_dotenv()

app = Flask(__name__)

# Configure basic console logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sysman-emulator")

# Config path for Secret Manager mounted volume
SYSTEMS_CONFIG_PATH = os.getenv("SYSTEMS_CONFIG_PATH", "")
CONTROL_HEADER = os.getenv("CONTROL_HEADER", "X-Control-Password")
CONTROL_PASSWORD = os.getenv("CONTROL_PASSWORD", "SysManSecretPass123!")


class ConfigDrivenSystemState:
    """Manages baseline telemetry, uptime, syslog entries, dynamic metrics variation, and command effects based on JSON configurations."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initializes system baseline state from a JSON configuration block."""
        self.system_id: str = config["system_id"]
        self.system_type: str = config["type"]
        self.name: str = config["name"]
        self.status: str = config.get("status", "HEALTHY")
        self.start_time: float = time.time()
        self.logs: List[Dict[str, Any]] = []
        self.last_update: float = time.time()
        
        # Loaded dynamic definitions
        self.default_icon: str = config.get("default_icon", "business_center")
        self.metrics: List[Dict[str, Any]] = config.get("metrics", [])
        self.actions: List[Dict[str, Any]] = config.get("actions", [])
        
        # Reboot sequence state
        self.reboot_started_at: Optional[float] = None
        self.reboot_duration: float = 5.0
        
        self.add_log(f"Config-driven system {self.name} ({self.system_id}) initialized.")

    def add_log(self, message: str, level: str = "INFO") -> None:
        """Appends a timestamped log to the syslog stream."""
        now = datetime.now(timezone.utc)
        self.logs.append({
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "timestamp_iso": now.isoformat(),
            "timestamp_epoch": time.time(),
            "level": level.upper(),
            "message": message,
        })
        if len(self.logs) > 100:
            self.logs.pop(0)

    @property
    def uptime_seconds(self) -> int:
        """Calculates current uptime."""
        return int(time.time() - self.start_time)

    def update_metrics(self) -> None:
        """Updates internal state and metrics by simulating dynamic drifts and variations."""
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now

        # 1. Handle reboot transition sequence
        if self.status == "REBOOTING":
            if self.reboot_started_at and (now - self.reboot_started_at >= self.reboot_duration):
                self.status = "HEALTHY"
                self.reboot_started_at = None
                self.add_log("System boot completed. Services restored.")
                # Reset metric statuses to healthy baseline
                for m in self.metrics:
                    if m["id"] == "node-exporter-status":
                        m["value"] = 1.0
                    elif m["id"] == "ws-status":
                        m["value"] = 1.0
            return

        # 2. Iterate and update dynamic metric values
        for m in self.metrics:
            # Apply systematic drifts (e.g. JVM memory leaks)
            drift = m.get("drift_rate", 0.0)
            if drift != 0.0:
                m["value"] += drift

            # Apply random variations
            var_range = m.get("variation_range")
            if var_range and len(var_range) == 2:
                m["value"] += random.uniform(var_range[0], var_range[1])

            # Enforce clamp boundaries
            min_lim = m.get("min_value_limit")
            max_lim = m.get("max_value_limit")
            if min_lim is not None:
                m["value"] = max(min_lim, m["value"])
            if max_lim is not None:
                m["value"] = min(max_lim, m["value"])

            # Compute val_text using format template
            fmt = m.get("val_text_format", "{value}")
            try:
                m["val_text"] = fmt.format(value=m["value"], max_value=m.get("max_value", 0.0))
            except Exception:
                m["val_text"] = str(m["value"])

            # Evaluate status rules and alerts
            if "status_rules" in m:
                matched_rule = False
                for rule in m["status_rules"]:
                    operator = rule.get("operator", "==")
                    target = rule.get("target")
                    rule_status = rule.get("status", "healthy")
                    rule_text = rule.get("val_text")
                    
                    val = m["value"]
                    match = False
                    if operator == "==":
                        match = abs(val - target) < 0.001
                    elif operator == ">=":
                        match = val >= target
                    elif operator == "<=":
                        match = val <= target
                    elif operator == ">":
                        match = val > target
                    elif operator == "<":
                        match = val < target
                    
                    if match:
                        m["status"] = rule_status
                        if rule_text:
                            m["val_text"] = rule_text
                        matched_rule = True
                        break
                if not matched_rule:
                    m["status"] = "healthy"

    def execute_command(self, command: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Runs an administrative system action and updates the internal state metrics accordingly."""
        self.update_metrics()
        
        # Locate matching command structure
        target_action = None
        for act in self.actions:
            if act["command"] == command:
                target_action = act
                break
        
        if not target_action:
            return {"error": f"Command '{command}' not recognized for this system"}, 400

        effects = target_action.get("effects", {})
        
        # Apply configured effects
        if "set_status" in effects:
            self.status = effects["set_status"]
            if self.status == "REBOOTING":
                self.reboot_started_at = time.time()

        if "metrics" in effects:
            for m_id, change in effects["metrics"].items():
                for m in self.metrics:
                    if m["id"] == m_id:
                        if "set" in change:
                            m["value"] = change["set"]
                        if "drift_rate" in change:
                            m["drift_rate"] = change["drift_rate"]

        if "log" in effects:
            log_conf = effects["log"]
            self.add_log(log_conf.get("message", "Action executed."), log_conf.get("level", "INFO"))

        return {"status": "SUCCESS", "message": f"Command '{command}' executed successfully"}, 200

    def to_dict(self) -> Dict[str, Any]:
        """Serializes current config-driven state."""
        self.update_metrics()
        return {
            "system_id": self.system_id,
            "type": self.system_type,
            "name": self.name,
            "status": self.status,
            "uptime_seconds": self.uptime_seconds,
            "default_icon": self.default_icon,
            "logs": self.logs[-15:],
            "metrics": self.metrics,
            "actions": self.actions
        }


# --- System Discovery and Initialization ---
SYSTEM_REGISTRY: Dict[str, ConfigDrivenSystemState] = {}
EMULATOR_CONFIG_PATH = os.getenv("EMULATOR_CONFIG_PATH", "").strip()


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
    req_auth = request.headers.get(CONTROL_HEADER, "")
    if not req_auth or req_auth != CONTROL_PASSWORD:
        logger.warning(f"Unauthorized command execution attempt from {request.remote_addr}")
        return jsonify({"error": "Unauthorized", "message": "Invalid or missing auth header"}), 401

    payload = request.get_json(silent=True) or {}
    sys_id = payload.get("system_id", "").strip()
    command = payload.get("command", "").strip()
    params = payload.get("parameters", {})

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
    app.run(host="127.0.0.1", port=port, debug=debug_mode)
