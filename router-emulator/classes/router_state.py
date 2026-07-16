"""Hardware Router Emulator State Management Class.

Encapsulates chassis LED state, uptime tracking, operational status, event logging,
and execution of operational hardware control commands.
"""

from collections import deque
from datetime import datetime, timezone
import json
import os
from string import Template
import time
from typing import Any, Dict, List, Optional, Tuple

from helpers.logger import setup_json_logging

logger = setup_json_logging("router-emulator.state")


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
        self.logs: deque = deque(maxlen=10000)

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
        """Appends a new event log entry to the in-memory FIFO log ring buffer.

        Args:
            message: Message text describing the hardware event.
            level: Severity level string (INFO, WARN, ERROR).
        """
        now_dt = datetime.now(timezone.utc)
        self.logs.append({
            "timestamp": now_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "timestamp_iso": now_dt.isoformat(),
            "timestamp_epoch": time.time(),
            "level": level.upper(),
            "message": message,
        })

    def get_logs(
        self,
        since_seconds: Optional[float] = None,
        since_iso: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Queries historical hardware action logs collected in memory.

        Args:
            since_seconds: Filter log entries within the last N seconds.
            since_iso: ISO 8601 string timestamp cutoff.
            level: Filter by severity level string (e.g. INFO, WARN, ERROR).
            limit: Maximum number of log entries to return (default: 100).

        Returns:
            List of matching hardware action log entry dictionaries.
        """
        now = time.time()
        filtered = list(self.logs)

        if since_seconds is not None and since_seconds > 0:
            cutoff = now - since_seconds
            window_matches = [entry for entry in filtered if entry.get("timestamp_epoch", 0.0) >= cutoff]
            if window_matches:
                filtered = window_matches
        elif since_iso:
            try:
                dt = datetime.fromisoformat(since_iso.replace("Z", "+00:00"))
                cutoff = dt.timestamp()
                window_matches = [entry for entry in filtered if entry.get("timestamp_epoch", 0.0) >= cutoff]
                if window_matches:
                    filtered = window_matches
            except ValueError:
                pass

        if level:
            lvl_upper = level.upper()
            filtered = [entry for entry in filtered if entry.get("level", "INFO").upper() == lvl_upper]

        return filtered[-limit:]

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
            "logs": list(self.logs)[-25:],
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

        logger.debug(
            f"Executing state command '{self.last_command}' with params {params} "
            f"for router '{self.router_id}' from controller '{remote_addr}'"
        )

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
                self.status = "BGP_FAULT"
                self.leds.update({
                    "upstream": "red",
                    "online": "amber",
                    "send": "off",
                    "receive": "off",
                })
                self.add_log(
                    f"CRITICAL FAULT: Immediate BGP upstream peering session collapse injected by controller ({remote_addr}).",
                    "ERROR"
                )
                msg = "Fail Mode ENABLED - Immediate BGP upstream fault injected"
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

    def to_a2ui_card_manifest(self) -> str:
        """Constructs and returns the dynamic A2UI v0.8 card manifest string for this router node.

        Returns:
            String containing <a2ui-json> enclosed manifest payload.
        """
        base_dir = os.path.dirname(os.path.dirname(__file__))
        template_path = os.path.join(base_dir, "a2ui_templates", "card.json")

        def get_led_info(name_key: str, label: str):
            val = str(self.leds.get(name_key, "off")).lower()
            if "green" in val or "flash" in val:
                return f"🟢 {label}", "#00FF00"
            elif "amber" in val or "yellow" in val:
                return f"🟠 {label}", "#FFA500"
            elif "red" in val:
                return f"🔴 {label}", "#FF0000"
            else:
                return f"⚫ {label}", "#808080"

        onli_txt, onli_clr = get_led_info("online", "ONLI")
        upst_txt, upst_clr = get_led_info("upstream", "UPST")
        lan1_txt, lan1_clr = get_led_info("lan1", "LAN1")
        lan2_txt, lan2_clr = get_led_info("lan2", "LAN2")
        lan3_txt, lan3_clr = get_led_info("lan3", "LAN3")
        lan4_txt, lan4_clr = get_led_info("lan4", "LAN4")
        send_txt, send_clr = get_led_info("send", "SEND")
        recv_txt, recv_clr = get_led_info("receive", "RECV")

        surface_id = f"router-card-{self.router_id.lower().replace('-', '_')}-{int(time.time() * 1000)}"

        values = {
            "surface_id": surface_id,
            "display_name": self.router_id,
            "router_id": self.router_id,
            "subtitle": self.purpose,
            "location": self.location,
            "uptime": f"{self.uptime_seconds}s",
            "state": self.status,
            "mfg_model": f"{self.manufacturer} {self.firmware_version}",
            "led_onli_text": onli_txt,
            "led_onli_color": onli_clr,
            "led_upst_text": upst_txt,
            "led_upst_color": upst_clr,
            "led_lan1_text": lan1_txt,
            "led_lan1_color": lan1_clr,
            "led_lan2_text": lan2_txt,
            "led_lan2_color": lan2_clr,
            "led_lan3_text": lan3_txt,
            "led_lan3_color": lan3_clr,
            "led_lan4_text": lan4_txt,
            "led_lan4_color": lan4_clr,
            "led_send_text": send_txt,
            "led_send_color": send_clr,
            "led_recv_text": recv_txt,
            "led_recv_color": recv_clr,
        }

        if os.path.exists(template_path):
            try:
                with open(template_path, "r", encoding="utf-8") as f:
                    template_str = f.read()
                rendered_json_str = Template(template_str).safe_substitute(values)
                payload = json.loads(rendered_json_str)
                return f"<a2ui-json>\n{json.dumps(payload, indent=2)}\n</a2ui-json>"
            except Exception as err:
                logger.warning(f"Failed loading A2UI card template at '{template_path}': {err}")

        # Fallback to telemetry dictionary
        return f"<a2ui-json>\n{json.dumps(self.to_telemetry_dict(), indent=2)}\n</a2ui-json>"

    def to_a2ui_image_card_manifest(self) -> str:
        """Constructs an A2UI v0.8 card manifest containing an embedded Base64 PNG snapshot image.

        Returns:
            String containing <a2ui-json> enclosed manifest payload.
        """
        import base64
        png_bytes = self.render_png_card_bytes()
        base64_png = base64.b64encode(png_bytes).decode("utf-8")
        data_uri = f"data:image/png;base64,{base64_png}"

        surface_id = f"router-card-image-{self.router_id.lower().replace('-', '_')}"

        payload = [
            {
                "beginRendering": {
                    "surfaceId": surface_id,
                    "root": "card-root"
                }
            },
            {
                "surfaceUpdate": {
                    "surfaceId": surface_id,
                    "components": [
                        {
                            "id": "card-root",
                            "component": {
                                "Card": {
                                    "child": "image-comp",
                                    "style": {
                                        "backgroundColor": "#0B131E",
                                        "borderRadius": "12px",
                                        "padding": "8px"
                                    }
                                }
                            }
                        },
                        {
                            "id": "image-comp",
                            "component": {
                                "Image": {
                                    "url": {
                                        "literalString": data_uri
                                    },
                                    "fit": "contain"
                                }
                            }
                        }
                    ]
                }
            }
        ]

        return f"<a2ui-json>\n{json.dumps(payload, indent=2)}\n</a2ui-json>"

    def render_png_card_bytes(self) -> bytes:
        """Constructs a high-fidelity, high-resolution (1200x530) PNG visual card representation using PIL.

        Returns:
            Raw PNG bytes stream.
        """
        import io
        from PIL import Image, ImageDraw, ImageFont

        width, height = 1200, 530
        img = Image.new("RGBA", (width, height), color=(11, 19, 30, 255))
        draw = ImageDraw.Draw(img)

        # Resolve a scalable TrueType font if available, fallback to default
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
        selected_path = None
        for path in font_paths:
            try:
                ImageFont.truetype(path, 12)
                selected_path = path
                break
            except Exception:
                continue

        def get_font(size: int):
            if selected_path:
                return ImageFont.truetype(selected_path, size)
            return ImageFont.load_default(size=size)

        title_font = get_font(36)
        header_font = get_font(24)
        label_font = get_font(24)
        value_font = get_font(24)
        led_font = get_font(20)
        btn_font = get_font(22)

        # Outer card rounded rectangle border with cyan accent
        draw.rounded_rectangle(
            [(20, 20), (width - 20, height - 20)],
            radius=24,
            outline=(0, 176, 255, 255),
            width=4,
        )

        # Draw Header Section
        draw.text((60, 45), f"🌐  {self.router_id}", font=title_font, fill=(0, 176, 255, 255))
        draw.text((60, 95), f"Purpose:  {self.purpose}", font=header_font, fill=(0, 176, 255, 255))
        draw.text((60, 130), f"Location: {self.location}", font=header_font, fill=(0, 176, 255, 255))

        # Horizontal Divider 1
        draw.line([(60, 170), (width - 60, 170)], fill=(0, 176, 255, 120), width=2)

        # Key / Value Telemetry Table Grid
        draw.text((60, 195), "Display Name:", font=label_font, fill=(0, 255, 255, 255))
        draw.text((320, 195), f"{self.router_id}", font=value_font, fill=(0, 255, 255, 255))

        draw.text((60, 235), "Uptime:", font=label_font, fill=(50, 205, 50, 255))
        draw.text((320, 235), f"{self.uptime_seconds}s", font=value_font, fill=(50, 205, 50, 255))

        draw.text((60, 275), "State:", font=label_font, fill=(50, 205, 50, 255))
        draw.text((320, 275), f"{self.status}", font=value_font, fill=(50, 205, 50, 255))

        draw.text((60, 315), "MFG/Model:", font=label_font, fill=(0, 255, 255, 255))
        draw.text((320, 315), f"{self.manufacturer} {self.firmware_version}", font=value_font, fill=(0, 255, 255, 255))

        # Horizontal Divider 2
        draw.line([(60, 360), (width - 60, 360)], fill=(0, 176, 255, 120), width=2)

        # Glowing Circular LED Indicators Status Bar
        current_leds = self.leds
        led_names = ["online", "upstream", "lan1", "lan2", "lan3", "lan4", "send", "receive"]

        # LED status bar container background pill box
        draw.rounded_rectangle(
            [(60, 380), (width - 60, 490)],
            radius=16,
            fill=(7, 12, 20, 255),
            outline=(40, 60, 80, 255),
            width=2,
        )

        start_x = 125
        step_x = 135
        cy = 422

        for idx, led_name in enumerate(led_names):
            cx = start_x + (idx * step_x)

            color_str = str(current_leds.get(led_name, "off")).lower()
            if "green" in color_str:
                fill_color = (0, 255, 0, 255)
                glow_color = (0, 255, 0, 60)
            elif "amber" in color_str or "yellow" in color_str:
                fill_color = (255, 165, 0, 255)
                glow_color = (255, 165, 0, 60)
            elif "red" in color_str:
                fill_color = (255, 0, 0, 255)
                glow_color = (255, 0, 0, 60)
            else:
                fill_color = (60, 60, 60, 255)
                glow_color = (40, 40, 40, 30)

            # Draw outer glow circle
            draw.ellipse([(cx - 18, cy - 18), (cx + 18, cy + 18)], fill=glow_color)
            # Draw primary LED bulb
            draw.ellipse([(cx - 12, cy - 12), (cx + 12, cy + 12)], fill=fill_color)

            # Centered LED Label
            lbl = led_name.upper()[:4]
            draw.text((cx, cy + 42), lbl, font=led_font, fill=(220, 235, 250, 255), anchor="ms")



        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
