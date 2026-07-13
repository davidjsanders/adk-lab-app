"""Hardware Router Emulator State Management Class.

Encapsulates chassis LED state, uptime tracking, operational status, event logging,
and execution of operational hardware control commands.
"""

from datetime import datetime, timezone
import os
import time
from typing import Any, Dict, List, Tuple


class RouterState:
    """Manages physical router chassis state, LED indicators, and operational telemetry.

    Attributes:
        router_id: Unique string identifier for the router node.
        location: Physical location description string.
        purpose: Operational purpose description string.
        manufacturer: Equipment manufacturer ID string.
        firmware_version: Running firmware version string.
        start_time: POSIX timestamp when the router node was initialized.
        leds: Dictionary mapping chassis LED names to current color states.
        status: Current operational status string (e.g. OPERATIONAL, BOOTING, POWERED_OFF).
        booting: Boolean flag indicating if system is currently executing boot sequence.
        last_command: String representation of last executed command.
        last_command_time: ISO 8601 UTC timestamp of last executed command.
        logs: Historical log entries list.
    """

    VALID_LEDS: List[str] = [
        "power", "online", "upstream", "lan1", "lan2", "lan3", "lan4", "send", "receive"
    ]
    VALID_COLORS: List[str] = [
        "red", "amber", "green", "off", "flash", "flash_fast"
    ]

    def __init__(
        self,
        router_id: str = "RTR-CORE-01",
        location: str = "Data Center Alpha - Rack 12B",
        purpose: str = "Primary Edge Core Router",
        manufacturer: str = "CISCO-NEXUS-9000-X",
        firmware_version: str = "v4.18.2-LTS",
    ) -> None:
        """Initializes a new RouterState instance with default operational parameters.

        Args:
            router_id: Unique router node identifier.
            location: Physical datacenter location description.
            purpose: Hardware purpose description.
            manufacturer: Manufacturer ID string.
            firmware_version: Software/firmware version.
        """
        self.router_id: str = router_id
        self.location: str = location
        self.purpose: str = purpose
        self.manufacturer: str = manufacturer
        self.firmware_version: str = firmware_version
        self.start_time: float = time.time()

        self.leds: Dict[str, str] = {
            "power": "green",
            "online": "green",
            "upstream": "green",
            "lan1": "green",
            "lan2": "green",
            "lan3": "off",
            "lan4": "off",
            "send": "flash",
            "receive": "flash",
        }

        self.status: str = "OPERATIONAL"
        self.booting: bool = False
        self.last_command: str = "INITIALIZED"
        self.last_command_time: str = datetime.now(timezone.utc).isoformat()
        self.logs: List[Dict[str, str]] = []

        # Activity Timeout & Auto-Sleep Configuration
        self.last_activity_time: float = time.time()
        self.inactivity_timeout: float = float(os.getenv("INACTIVITY_TIMEOUT_SECONDS", "30.0"))
        self.is_idle_sleeping: bool = False

        # Timed Boot Sequence Configuration
        self.boot_start_time: float = 0.0
        self.boot_duration: float = 6.0

        # Fail Mode & Automated Fault Injection Configuration
        self.fail_mode: bool = False
        self.last_fail_time: float = 0.0
        self.fail_interval: float = float(os.getenv("FAIL_MODE_INTERVAL_SECONDS", "300.0"))

        self.add_log(f"Router {self.router_id} system initialized and online.")

    def check_fail_mode(self) -> None:
        """Evaluates active fail mode state and injects BGP failures every 5 minutes when active."""
        if self.fail_mode and self.status == "OPERATIONAL":
            now = time.time()
            if self.last_fail_time == 0.0:
                self.last_fail_time = now
            elif now - self.last_fail_time >= self.fail_interval:
                self.last_fail_time = now
                self.status = "BGP_FAULT"
                self.leds.update({
                    "upstream": "red",
                    "online": "amber",
                    "send": "off",
                    "receive": "off",
                })
                self.add_log(
                    "CRITICAL FAULT: Injected automatic BGP peering session collapse (AS 65001 peer down).",
                    "ERROR"
                )

    def check_boot_sequence(self) -> None:
        """Evaluates active POST boot sequence and transitions to OPERATIONAL after boot duration."""
        if self.booting and self.boot_start_time > 0:
            elapsed = time.time() - self.boot_start_time
            if elapsed >= self.boot_duration:
                self.booting = False
                self.status = "OPERATIONAL"
                self.leds.update({
                    "power": "green",
                    "online": "green",
                    "upstream": "green",
                    "lan1": "green",
                    "lan2": "green",
                    "send": "flash",
                    "receive": "flash"
                })
                self.add_log("System POST boot diagnostics complete. Router status is OPERATIONAL.")

    def touch_activity(self) -> None:
        """Resets the last recorded activity timestamp and resumes operation if sleeping."""
        self.last_activity_time = time.time()
        if self.is_idle_sleeping:
            self.is_idle_sleeping = False
            if self.status == "SLEEPING":
                self.status = "OPERATIONAL"
                self.leds.update({"send": "flash", "receive": "flash", "online": "green"})
                self.add_log("Dashboard heartbeat detected. Resuming operational telemetry processing.")

    def check_inactivity(self) -> None:
        """Checks if maximum inactivity threshold has elapsed since last dashboard query."""
        if time.time() - self.last_activity_time > self.inactivity_timeout:
            if not self.is_idle_sleeping and self.status == "OPERATIONAL":
                self.is_idle_sleeping = True
                self.status = "SLEEPING"
                self.leds.update({"send": "off", "receive": "off", "online": "amber"})
                self.add_log(
                    f"No dashboard traffic detected for {int(self.inactivity_timeout)}s. Entering auto-sleep mode.",
                    "WARN"
                )

    def add_log(self, message: str, level: str = "INFO") -> None:
        """Appends a new event log entry to the in-memory log buffer.

        Args:
            message: Message text describing the hardware event.
            level: Severity level string (INFO, WARN, ERROR).
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        self.logs.append({
            "timestamp": timestamp,
            "level": level,
            "message": message,
        })
        if len(self.logs) > 100:
            self.logs.pop(0)

    @property
    def uptime_seconds(self) -> int:
        """Calculates current system uptime in seconds.

        Returns:
            Elapsed uptime in seconds.
        """
        return int(time.time() - self.start_time)

    def to_telemetry_dict(self) -> Dict[str, Any]:
        """Serializes current router telemetry and LED state into a API response dictionary.

        Returns:
            Dictionary containing metadata, telemetry, LED indicators, and event logs.
        """
        self.check_boot_sequence()
        self.check_inactivity()
        self.check_fail_mode()
        current_leds = self.leds.copy()
        if self.status == "OPERATIONAL" and self.last_command != "SET_LED":
            # Introduce dynamic traffic flicker dynamics unique to this router node ID and timestamp
            node_hash = sum(ord(c) for c in self.router_id)
            cycle = int(time.time() * 1.5) + node_hash
            
            send_states = ["flash", "flash_fast", "green", "flash"]
            recv_states = ["flash_fast", "flash", "green", "flash"]
            
            current_leds["send"] = send_states[cycle % len(send_states)]
            current_leds["receive"] = recv_states[(cycle + 2) % len(recv_states)]

        return {
            "metadata": {
                "router_id": self.router_id,
                "location": self.location,
                "purpose": self.purpose,
                "manufacturer_id": self.manufacturer,
                "firmware_version": self.firmware_version,
            },
            "telemetry": {
                "uptime_seconds": self.uptime_seconds,
                "status": self.status,
                "booting": self.booting,
                "fail_mode": self.fail_mode,
                "last_command": self.last_command,
                "last_command_time": self.last_command_time,
            },
            "leds": current_leds,
            "logs": self.logs[-25:],
        }

    def execute_command(
        self, command: str, params: Dict[str, Any], remote_addr: str = "127.0.0.1"
    ) -> Tuple[Dict[str, Any], int]:
        """Executes an operational control command against the router chassis state.

        Args:
            command: Command keyword string (e.g. power_up, power_down, reset, bgp_reset, set_fail_mode, set_led).
            params: Parameters dictionary (e.g. {"led": "power", "color": "green"}).
            remote_addr: IP address string of the requesting client controller.

        Returns:
            Tuple of (response_dict, HTTP_status_code).

        Raises:
            ValueError if invalid arguments are provided.
        """
        cmd_clean = command.lower().strip()
        timestamp = datetime.now(timezone.utc).isoformat()
        self.last_command = cmd_clean.upper()
        self.last_command_time = timestamp

        if cmd_clean in ("power_up", "powerup", "start"):
            self.leds.update({
                "power": "green",
                "online": "green",
                "upstream": "green",
                "lan1": "green",
                "lan2": "green",
                "send": "flash",
                "receive": "flash",
            })
            self.status = "OPERATIONAL"
            self.booting = False
            self.add_log(f"Command executed: POWER UP by controller ({remote_addr})")
            return {"status": "SUCCESS", "message": "Router powered up successfully", "state": self.to_telemetry_dict()}, 200

        elif cmd_clean in ("power_down", "powerdown", "shutdown", "stop"):
            self.leds.update({
                "power": "red",
                "online": "off",
                "upstream": "off",
                "lan1": "off",
                "lan2": "off",
                "lan3": "off",
                "lan4": "off",
                "send": "off",
                "receive": "off",
            })
            self.status = "POWERED_OFF"
            self.booting = False
            self.add_log(f"Command executed: POWER DOWN by controller ({remote_addr})", "WARN")
            return {"status": "SUCCESS", "message": "Router powered down", "state": self.to_telemetry_dict()}, 200

        elif cmd_clean in ("reset", "reboot", "boot"):
            self.status = "BOOTING"
            self.booting = True
            self.boot_start_time = time.time()
            self.leds.update({
                "power": "green",
                "online": "flash",
                "upstream": "amber",
                "send": "off",
                "receive": "off",
            })
            self.add_log(f"Command executed: SYSTEM REBOOT initiated by controller ({remote_addr})")
            return {"status": "SUCCESS", "message": "Boot sequence initiated (6s POST sequence)", "state": self.to_telemetry_dict()}, 200

        elif cmd_clean in ("bgp_reset", "bgp_restart"):
            self.fail_mode = False  # Turn fail mode off when user resets BGP!
            self.status = "OPERATIONAL"
            self.leds.update({
                "power": "green",
                "online": "green",
                "upstream": "green",
                "send": "flash",
                "receive": "flash",
            })
            self.add_log(f"Command executed: BGP RESET by controller ({remote_addr}). Session restored & Fail Mode set to OFF.")
            return {
                "status": "SUCCESS",
                "message": "BGP peer session re-established. Fail mode turned OFF.",
                "state": self.to_telemetry_dict(),
            }, 200

        elif cmd_clean in ("set_fail_mode", "fail_mode", "toggle_fail"):
            enabled = bool(params.get("enabled", True))
            self.fail_mode = enabled
            if enabled:
                self.last_fail_time = time.time()
                self.add_log(f"Command executed: FAIL MODE ENABLED by controller ({remote_addr}) - 5min fault injection active.", "WARN")
                msg = "Fail Mode ENABLED - Automated 5-min BGP fault injection active"
            else:
                self.add_log(f"Command executed: FAIL MODE DISABLED by controller ({remote_addr})")
                msg = "Fail Mode DISABLED"
            return {"status": "SUCCESS", "message": msg, "state": self.to_telemetry_dict()}, 200

        elif cmd_clean in ("send_info", "simulate_traffic", "traffic_burst"):
            self.leds.update({
                "send": "flash_fast",
                "receive": "flash_fast",
            })
            self.add_log(f"Command executed: TRAFFIC BURST simulated by controller ({remote_addr})")
            return {
                "status": "SUCCESS",
                "message": "Simulated packet transmission burst initiated",
                "state": self.to_telemetry_dict(),
            }, 200

        elif cmd_clean == "set_led":
            target_led = str(params.get("led", "")).lower()
            color = str(params.get("color", "")).lower()

            if target_led not in self.VALID_LEDS or color not in self.VALID_COLORS:
                return {
                    "error": "Bad Request",
                    "message": f"Invalid LED target or color. Allowed LEDs: {self.VALID_LEDS}, Colors: {self.VALID_COLORS}",
                }, 400

            self.leds[target_led] = color
            self.add_log(f"Command executed: SET_LED {target_led.upper()} -> {color.upper()}")
            return {"status": "SUCCESS", "message": f"LED {target_led} set to {color}", "state": self.to_telemetry_dict()}, 200

        else:
            return {
                "error": "Bad Request",
                "message": f"Unrecognized command '{cmd_clean}'. Valid commands: power_up, power_down, reset, bgp_reset, send_info, set_led",
            }, 400
