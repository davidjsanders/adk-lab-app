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


class BaseSystemState:
    """Manages baseline telemetry, uptime, and syslog triggers for all system models."""

    def __init__(self, system_id: str, system_type: str, name: str) -> None:
        """Initializes system baseline state.

        Args:
            system_id: Unique string identifier for the system node.
            system_type: Category of the system (linux, jira, confluence).
            name: Friendly display name.
        """
        self.system_id: str = system_id
        self.system_type: str = system_type
        self.name: str = name
        self.status: str = "HEALTHY"
        self.start_time: float = time.time()
        self.logs: List[Dict[str, Any]] = []
        self.last_update: float = time.time()
        self.add_log(f"System {self.name} ({self.system_id}) initialized successfully.")

    def add_log(self, message: str, level: str = "INFO") -> None:
        """Appends a timestamped log to the host syslog stream.

        Args:
            message: Text description of the log event.
            level: Severity level (INFO, WARN, ERROR).
        """
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
        """Calculates current uptime.

        Returns:
            Total system uptime in seconds.
        """
        return int(time.time() - self.start_time)

    def update_metrics(self) -> None:
        """Abstract method to update internal metrics on check interval."""
        pass

    def execute_command(self, command: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Abstract method for command routing.

        Args:
            command: Cleaned command keyword string.
            params: Parameters dictionary.

        Returns:
            Tuple of response payload dict and HTTP status code.
        """
        return {"error": "Method not implemented"}, 501

    def to_dict(self) -> Dict[str, Any]:
        """Serializes current state telemetry to dictionary.

        Returns:
            Dictionary containing system metadata and metrics.
        """
        self.update_metrics()
        return {
            "system_id": self.system_id,
            "type": self.system_type,
            "name": self.name,
            "status": self.status,
            "uptime_seconds": self.uptime_seconds,
            "logs": self.logs[-15:]
        }


class LinuxSystemState(BaseSystemState):
    """Emulates a Linux server running node_exporter telemetry."""

    def __init__(self, system_id: str, system_type: str, name: str) -> None:
        """Initializes Linux system state variables."""
        super().__init__(system_id, system_type, name)
        self.cpu_load: float = 22.5
        self.ram_usage_percent: float = 45.0
        self.disk_usage_percent: float = 58.2
        self.process_down: int = 1  # 1 = node_exporter UP, 0 = node_exporter DOWN
        self.anomaly_active: bool = False

    def update_metrics(self) -> None:
        """Updates simulated Linux system metrics with dynamic variations."""
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now

        if self.status == "REBOOTING":
            if elapsed > 5.0 or self.uptime_seconds > 5:
                self.status = "HEALTHY"
                self.process_down = 1
                self.cpu_load = 15.0
                self.add_log("System boot completed. Services started.")
            else:
                self.cpu_load = 99.0
                self.ram_usage_percent = 90.0
                return

        # Normal random variations
        if self.process_down == 1:
            self.cpu_load = max(5.0, min(95.0, self.cpu_load + random.uniform(-2.0, 2.0)))
            self.ram_usage_percent = max(10.0, min(95.0, self.ram_usage_percent + random.uniform(-0.5, 0.5)))
            self.disk_usage_percent = min(100.0, self.disk_usage_percent + random.uniform(0.0001, 0.001))
            self.status = "HEALTHY"
        else:
            # node_exporter is down - anomaly!
            self.cpu_load = max(1.0, min(20.0, self.cpu_load + random.uniform(-1.0, 1.0)))
            self.ram_usage_percent = max(10.0, min(30.0, self.ram_usage_percent - random.uniform(0.1, 0.5)))
            self.status = "UNHEALTHY"

        if self.anomaly_active and self.process_down == 1:
            self.cpu_load = max(85.0, self.cpu_load + random.uniform(-1.0, 2.0))
            self.ram_usage_percent = max(88.0, self.ram_usage_percent + random.uniform(-0.2, 0.4))
            self.status = "UNHEALTHY"

    def execute_command(self, command: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Executes operational commands on Linux VM.

        Args:
            command: Command keyword string.
            params: Parameters dictionary.

        Returns:
            Tuple of response payload dict and HTTP status code.
        """
        cmd_clean = command.upper().strip()
        if cmd_clean == "REBOOT":
            self.status = "REBOOTING"
            self.start_time = time.time()
            self.process_down = 0
            self.add_log("Reboot command received. System restarting...", "WARN")
            return {"status": "SUCCESS", "message": "System reboot initiated"}, 200

        elif cmd_clean == "STOP_NODE_EXPORTER":
            self.process_down = 0
            self.add_log("Service node_exporter stopped by admin control.", "WARN")
            return {"status": "SUCCESS", "message": "node_exporter stopped"}, 200

        elif cmd_clean == "START_NODE_EXPORTER":
            self.process_down = 1
            self.add_log("Service node_exporter started successfully.")
            return {"status": "SUCCESS", "message": "node_exporter started"}, 200

        elif cmd_clean == "INJECT_FAULT":
            self.anomaly_active = True
            self.add_log("Injected simulated high CPU load anomaly.", "ERROR")
            return {"status": "SUCCESS", "message": "Fault injected successfully"}, 200

        elif cmd_clean == "CLEAR_FAULT":
            self.anomaly_active = False
            self.add_log("Cleared simulated high CPU load anomaly.")
            return {"status": "SUCCESS", "message": "Fault cleared"}, 200

        return {"error": f"Command '{command}' not recognized for Linux systems"}, 400

    def to_dict(self) -> Dict[str, Any]:
        """Serializes Linux metrics.

        Returns:
            Linux telemetry status payload.
        """
        data = super().to_dict()
        data["raw_metrics"] = {
            "cpu_load_percent": round(self.cpu_load, 1),
            "ram_usage_percent": round(self.ram_usage_percent, 1),
            "disk_usage_percent": round(self.disk_usage_percent, 2),
            "process_down": self.process_down
        }
        data["metrics"] = [
            {
                "id": "cpu-load",
                "type": "donut_chart",
                "label": "CPU Usage",
                "value": round(self.cpu_load, 1),
                "max_value": 100.0,
                "val_text": f"{self.cpu_load:.1f}%"
            },
            {
                "id": "node-exporter-status",
                "type": "status_pill",
                "label": "node_exporter",
                "value": self.process_down,
                "status": "healthy" if self.process_down == 1 else "critical",
                "val_text": "RUNNING" if self.process_down == 1 else "STOPPED"
            }
        ]
        data["actions"] = [
            {"id": "btn-reboot", "type": "button", "label": "Reboot VM", "command": "REBOOT", "color": "#EF4444"},
            {
                "id": "btn-toggle-exporter",
                "type": "button",
                "label": "Stop exporter" if self.process_down == 1 else "Start exporter",
                "command": "STOP_NODE_EXPORTER" if self.process_down == 1 else "START_NODE_EXPORTER",
                "color": "#EAB308" if self.process_down == 1 else "#22C55E"
            }
        ]
        return data


class JiraSystemState(BaseSystemState):
    """Emulates a Jira server running on JVM with DB connection pool monitoring."""

    def __init__(self, system_id: str, system_type: str, name: str) -> None:
        """Initializes Jira application state variables."""
        super().__init__(system_id, system_type, name)
        self.jvm_heap_mb: float = 1200.0
        self.jvm_max_heap_mb: float = 4096.0
        self.db_connections: int = 8
        self.db_pool_max: int = 50
        self.request_latency_ms: float = 125.0
        self.error_rate: float = 0.0
        self.leak_active: bool = False
        self.pool_exhaustion_active: bool = False

    def update_metrics(self) -> None:
        """Updates simulated Jira server metrics."""
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now

        if self.status == "REBOOTING":
            if elapsed > 8.0 or self.uptime_seconds > 8:
                self.status = "HEALTHY"
                self.jvm_heap_mb = 1100.0
                self.db_connections = 5
                self.request_latency_ms = 95.0
                self.error_rate = 0.0
                self.add_log("Jira Application server started successfully.")
            else:
                self.request_latency_ms = 9999.0
                self.error_rate = 100.0
                return

        # Memory leak logic (Drift)
        if self.leak_active:
            self.jvm_heap_mb = min(self.jvm_max_heap_mb, self.jvm_heap_mb + (10.0 * elapsed))
            if self.jvm_heap_mb / self.jvm_max_heap_mb > 0.95:
                # OOM State
                self.status = "UNHEALTHY"
                self.request_latency_ms = max(8000.0, self.request_latency_ms + random.uniform(500, 1000))
                self.error_rate = min(100.0, self.error_rate + random.uniform(5.0, 15.0))
                if random.random() < 0.1:
                    self.add_log("CRITICAL: OutOfMemoryError in Metaspace / Java Heap!", "ERROR")
            elif self.jvm_heap_mb / self.jvm_max_heap_mb > 0.8:
                self.status = "DEGRADED"
                self.request_latency_ms = max(1500.0, self.request_latency_ms + random.uniform(50, 200))
                self.error_rate = min(20.0, self.error_rate + random.uniform(0.1, 0.8))
                if random.random() < 0.05:
                    self.add_log("WARNING: JVM Garbage Collection taking too long (GC Overhead Limit Exceeded).", "WARN")
            else:
                self.jvm_heap_mb = max(500.0, self.jvm_heap_mb + random.uniform(-10.0, 15.0))
        else:
            # Baseline behavior
            self.jvm_heap_mb = max(800.0, min(3000.0, self.jvm_heap_mb + random.uniform(-30.0, 30.0)))

        # DB Connection pool exhaustion logic
        if self.pool_exhaustion_active:
            self.db_connections = min(self.db_pool_max, self.db_connections + int(random.uniform(1, 4)))
            if self.db_connections >= self.db_pool_max:
                self.status = "UNHEALTHY"
                self.request_latency_ms = max(5000.0, self.request_latency_ms + random.uniform(100, 400))
                self.error_rate = min(95.0, self.error_rate + random.uniform(2.0, 8.0))
                if random.random() < 0.1:
                    self.add_log("ERROR: Connection pool exhausted. Could not obtain JDBC Connection.", "ERROR")
            else:
                self.status = "DEGRADED"
                self.request_latency_ms = max(900.0, self.request_latency_ms + random.uniform(20, 80))
        else:
            self.db_connections = max(4, min(self.db_pool_max - 5, self.db_connections + random.choice([-1, 0, 1])))

        # Overall Status Resolution if not already overridden by anomalies
        if self.status not in ("DEGRADED", "UNHEALTHY", "REBOOTING"):
            self.request_latency_ms = max(60.0, min(300.0, self.request_latency_ms + random.uniform(-5.0, 5.0)))
            self.error_rate = max(0.0, min(2.0, self.error_rate + random.uniform(-0.1, 0.1)))
            self.status = "HEALTHY"

    def execute_command(self, command: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Executes operational commands on Jira application state.

        Args:
            command: Command keyword string.
            params: Parameters dictionary.

        Returns:
            Tuple of response payload dict and HTTP status code.
        """
        cmd_clean = command.upper().strip()
        if cmd_clean == "RESTART_JIRA":
            self.status = "REBOOTING"
            self.start_time = time.time()
            self.add_log("Jira Server restarted. Cleaning JVM cache...", "WARN")
            return {"status": "SUCCESS", "message": "Jira server restart triggered"}, 200

        elif cmd_clean == "GC_CLEANUP":
            self.jvm_heap_mb = 1050.0
            self.leak_active = False
            self.status = "HEALTHY"
            self.add_log("Forced system Garbage Collection. Freed unused Java heap memory.")
            return {"status": "SUCCESS", "message": "Garbage collection completed"}, 200

        elif cmd_clean == "EXPAND_DB_POOL":
            self.db_pool_max = 100
            self.pool_exhaustion_active = False
            self.status = "HEALTHY"
            self.add_log("Configuration updated. Expanded JDBC Pool limit to 100.")
            return {"status": "SUCCESS", "message": "DB pool expanded"}, 200

        elif cmd_clean == "EXHAUST_DB_POOL":
            self.pool_exhaustion_active = True
            self.add_log("Simulated connection pool leak triggered.", "ERROR")
            return {"status": "SUCCESS", "message": "DB Pool exhaustion triggered"}, 200

        elif cmd_clean == "TRIGGER_JVM_LEAK":
            self.leak_active = True
            self.add_log("Simulated memory leak triggered in class loader cache.", "ERROR")
            return {"status": "SUCCESS", "message": "JVM leak triggered"}, 200

        elif cmd_clean == "RESET_SIMULATION":
            self.leak_active = False
            self.pool_exhaustion_active = False
            self.status = "HEALTHY"
            self.jvm_heap_mb = 1200.0
            self.db_connections = 8
            self.db_pool_max = 50
            self.add_log("Simulation parameters reset to healthy baseline.")
            return {"status": "SUCCESS", "message": "Simulation states reset"}, 200

        return {"error": f"Command '{command}' not recognized for Jira systems"}, 400

    def to_dict(self) -> Dict[str, Any]:
        """Serializes Jira metrics.

        Returns:
            Jira status payload dict.
        """
        data = super().to_dict()
        data["raw_metrics"] = {
            "jvm_heap_mb": int(self.jvm_heap_mb),
            "jvm_max_heap_mb": int(self.jvm_max_heap_mb),
            "db_connections": self.db_connections,
            "db_pool_max": self.db_pool_max,
            "request_latency_ms": round(self.request_latency_ms, 1),
            "error_rate_percent": round(self.error_rate, 2)
        }
        
        heap_pct = (self.jvm_heap_mb / self.jvm_max_heap_mb) * 100.0 if self.jvm_max_heap_mb > 0 else 0.0
        
        err_status = "healthy"
        if self.error_rate >= 5.0:
            err_status = "critical"
        elif self.error_rate >= 1.0:
            err_status = "warning"

        data["metrics"] = [
            {
                "id": "jvm-heap",
                "type": "donut_chart",
                "label": "JVM Heap",
                "value": round(heap_pct, 1),
                "max_value": 100.0,
                "val_text": f"{heap_pct:.1f}%"
            },
            {
                "id": "db-connections",
                "type": "progress_bar",
                "label": "JDBC DB Connections",
                "value": self.db_connections,
                "max_value": self.db_pool_max,
                "val_text": f"{self.db_connections} / {self.db_pool_max}"
            },
            {
                "id": "request-latency",
                "type": "range_gauge",
                "label": "Request Latency",
                "value": round(self.request_latency_ms, 1),
                "max_value": 300.0,
                "yellow_threshold": 150.0,
                "red_threshold": 250.0,
                "val_text": f"{self.request_latency_ms:.1f} ms"
            },
            {
                "id": "error-rate",
                "type": "status_pill",
                "label": "5xx Error Rate",
                "value": round(self.error_rate, 2),
                "status": err_status,
                "val_text": f"{self.error_rate:.2f}%"
            }
        ]
        data["actions"] = [
            {"id": "btn-gc", "type": "button", "label": "Run GC", "command": "GC_CLEANUP", "color": "#38BDF8"},
            {"id": "btn-restart", "type": "button", "label": "Restart Jira", "command": "RESTART_JIRA", "color": "#EF4444"}
        ]
        return data


class ConfluenceSystemState(BaseSystemState):
    """Emulates a Confluence Wiki server with collaborative editor websocket and attachments storage monitoring."""

    def __init__(self, system_id: str, system_type: str, name: str) -> None:
        """Initializes Confluence Wiki state variables."""
        super().__init__(system_id, system_type, name)
        self.websocket_connected: int = 1  # 1 = connected, 0 = disconnected
        self.attachments_disk_percent: float = 48.5
        self.disk_fill_active: bool = False

    def update_metrics(self) -> None:
        """Updates Confluence system metrics."""
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now

        if self.status == "REBOOTING":
            if elapsed > 6.0 or self.uptime_seconds > 6:
                self.status = "HEALTHY"
                self.websocket_connected = 1
                self.add_log("Confluence service restarted. Synchronizer active.")
            else:
                self.websocket_connected = 0
                return

        # Disk fill anomaly logic
        if self.disk_fill_active:
            self.attachments_disk_percent = min(100.0, self.attachments_disk_percent + (5.0 * elapsed))
            if self.attachments_disk_percent >= 100.0:
                self.status = "UNHEALTHY"
                if random.random() < 0.1:
                    self.add_log("CRITICAL: Out of disk space on attachments volume /var/atlassian/confluence/attachments", "ERROR")
            elif self.attachments_disk_percent > 90.0:
                self.status = "DEGRADED"
                if random.random() < 0.05:
                    self.add_log("WARNING: Disk usage exceeded 90% threshold on attachments storage.", "WARN")
        else:
            self.attachments_disk_percent = min(100.0, max(10.0, self.attachments_disk_percent + random.uniform(-0.01, 0.01)))

        # Websocket status check
        if self.websocket_connected == 0:
            self.status = "DEGRADED" if self.status != "UNHEALTHY" else "UNHEALTHY"

        if self.websocket_connected == 1 and not self.disk_fill_active:
            self.status = "HEALTHY"

    def execute_command(self, command: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Executes operational commands on Confluence wiki state.

        Args:
            command: Command keyword string.
            params: Parameters dictionary.

        Returns:
            Tuple of response payload dict and HTTP status code.
        """
        cmd_clean = command.upper().strip()
        if cmd_clean == "REBOOT":
            self.status = "REBOOTING"
            self.start_time = time.time()
            self.websocket_connected = 0
            self.add_log("Triggered system reboot for Confluence wiki app.", "WARN")
            return {"status": "SUCCESS", "message": "Reboot sequence started"}, 200

        elif cmd_clean == "RECONNECT_WEBSOCKETS":
            self.websocket_connected = 1
            self.add_log("Synchronizer websocket manually re-established with collaborative editor server.")
            return {"status": "SUCCESS", "message": "Websockets connected"}, 200

        elif cmd_clean == "DROP_WEBSOCKETS":
            self.websocket_connected = 0
            self.add_log("Websocket connection aborted (Error 1006 Connection Drop).", "ERROR")
            return {"status": "SUCCESS", "message": "Websockets dropped"}, 200

        elif cmd_clean == "PURGE_ATTACHMENTS":
            self.attachments_disk_percent = 25.0
            self.disk_fill_active = False
            self.status = "HEALTHY"
            self.add_log("Manual attachments cleanup completed. Disk space freed.")
            return {"status": "SUCCESS", "message": "Disk purged"}, 200

        elif cmd_clean == "FILL_DISK":
            self.disk_fill_active = True
            self.add_log("Simulated disk storage fill attack triggered.", "ERROR")
            return {"status": "SUCCESS", "message": "Disk fill triggered"}, 200

        elif cmd_clean == "RESET_SIMULATION":
            self.disk_fill_active = False
            self.websocket_connected = 1
            self.status = "HEALTHY"
            self.attachments_disk_percent = 48.5
            self.add_log("Confluence simulation states reset to default.")
            return {"status": "SUCCESS", "message": "Simulation states reset"}, 200

        return {"error": f"Command '{command}' not recognized for Confluence systems"}, 400

    def to_dict(self) -> Dict[str, Any]:
        """Serializes Confluence metrics.

        Returns:
            Confluence status payload dict.
        """
        data = super().to_dict()
        data["raw_metrics"] = {
            "websocket_connected": self.websocket_connected,
            "attachments_disk_percent": round(self.attachments_disk_percent, 1)
        }
        data["metrics"] = [
            {
                "id": "ws-status",
                "type": "status_pill",
                "label": "Collaborative Edit WebSockets",
                "value": self.websocket_connected,
                "status": "healthy" if self.websocket_connected == 1 else "critical",
                "val_text": "CONNECTED" if self.websocket_connected == 1 else "DISCONNECTED"
            },
            {
                "id": "disk-usage",
                "type": "progress_bar",
                "label": "Disk Usage",
                "value": round(self.attachments_disk_percent, 1),
                "max_value": 100.0,
                "val_text": f"{self.attachments_disk_percent:.1f}%"
            }
        ]
        data["actions"] = [
            {
                "id": "btn-toggle-ws",
                "type": "button",
                "label": "Drop WebSockets" if self.websocket_connected == 1 else "Reconnect WebSockets",
                "command": "DROP_WEBSOCKETS" if self.websocket_connected == 1 else "RECONNECT_WEBSOCKETS",
                "color": "#EF4444" if self.websocket_connected == 1 else "#22C55E"
            },
            {"id": "btn-purge", "type": "button", "label": "Purge Disk", "command": "PURGE_ATTACHMENTS", "color": "#EAB308"}
        ]
        return data


# --- System Discovery and Initialization ---
SYSTEM_REGISTRY: Dict[str, BaseSystemState] = {}


def load_topology() -> None:
    """Discovers and parses host definitions from SYSTEMS_CONFIG_PATH or defaults."""
    global SYSTEM_REGISTRY
    SYSTEM_REGISTRY.clear()

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

        if sys_type == "linux":
            SYSTEM_REGISTRY[sys_id] = LinuxSystemState(sys_id, sys_type, sys_name)
        elif sys_type == "jira":
            SYSTEM_REGISTRY[sys_id] = JiraSystemState(sys_id, sys_type, sys_name)
        elif sys_type == "confluence":
            SYSTEM_REGISTRY[sys_id] = ConfluenceSystemState(sys_id, sys_type, sys_name)
        else:
            # Fallback to standard Linux system
            SYSTEM_REGISTRY[sys_id] = LinuxSystemState(sys_id, sys_type, sys_name)


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

        # Generate standard prometheus lines
        lines.append(f'# HELP sysman_uptime_seconds Uptime of the system {s_id}')
        lines.append(f'# TYPE sysman_uptime_seconds gauge')
        lines.append(f'sysman_uptime_seconds{{system_id="{s_id}",type="{s_type}"}} {sys.uptime_seconds}')

        health_val = 1 if sys.status == "HEALTHY" else (2 if sys.status == "DEGRADED" else 0)
        lines.append(f'# HELP sysman_health_status Health of the system {s_id} (1=healthy, 2=degraded, 0=unhealthy)')
        lines.append(f'# TYPE sysman_health_status gauge')
        lines.append(f'sysman_health_status{{system_id="{s_id}",type="{s_type}"}} {health_val}')

        if isinstance(sys, LinuxSystemState):
            lines.append(f'sysman_cpu_load_percent{{system_id="{s_id}"}} {sys.cpu_load:.2f}')
            lines.append(f'sysman_ram_usage_percent{{system_id="{s_id}"}} {sys.ram_usage_percent:.2f}')
            lines.append(f'sysman_disk_usage_percent{{system_id="{s_id}"}} {sys.disk_usage_percent:.2f}')
            lines.append(f'process_down{{system_id="{s_id}"}} {sys.process_down}')
        elif isinstance(sys, JiraSystemState):
            lines.append(f'sysman_jvm_heap_mb{{system_id="{s_id}"}} {sys.jvm_heap_mb:.2f}')
            lines.append(f'sysman_jvm_max_heap_mb{{system_id="{s_id}"}} {sys.jvm_max_heap_mb:.2f}')
            lines.append(f'sysman_db_connections{{system_id="{s_id}"}} {sys.db_connections}')
            lines.append(f'sysman_db_pool_max{{system_id="{s_id}"}} {sys.db_pool_max}')
            lines.append(f'sysman_request_latency_ms{{system_id="{s_id}"}} {sys.request_latency_ms:.2f}')
            lines.append(f'sysman_error_rate_percent{{system_id="{s_id}"}} {sys.error_rate:.2f}')
        elif isinstance(sys, ConfluenceSystemState):
            lines.append(f'sysman_websocket_connected{{system_id="{s_id}"}} {sys.websocket_connected}')
            lines.append(f'sysman_attachments_disk_percent{{system_id="{s_id}"}} {sys.attachments_disk_percent:.2f}')

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
    app.run(host="127.0.0.1", port=port, debug=True)
