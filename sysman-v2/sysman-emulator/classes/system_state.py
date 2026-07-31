# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Config-driven system telemetry and control state manager."""

from datetime import datetime, timezone
import random
import time
from typing import Any, Dict, List, Optional, Tuple


class ConfigDrivenSystemState:
    """Manages baseline telemetry, uptime, syslog entries, dynamic metrics variation, and command effects based on JSON configurations."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initializes system baseline state from a JSON configuration block."""
        self.system_id: str = config["system_id"]
        self.system_type: str = config["type"]
        self.name: str = config["name"]
        self.status: str = config.get("status", "HEALTHY")
        self.description: str = config.get("description", "")
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
            "description": self.description,
            "uptime_seconds": self.uptime_seconds,
            "default_icon": self.default_icon,
            "logs": self.logs[-15:],
            "metrics": self.metrics,
            "actions": self.actions
        }
