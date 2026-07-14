"""Pydantic model definitions and Enum type constraints for FastMCP schema generation."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    POWER_UP = "POWER_UP"
    POWER_DOWN = "POWER_DOWN"
    REBOOT = "REBOOT"
    BGP_RESET = "BGP_RESET"
    BGP_FAULT = "BGP_FAULT"
    TRAFFIC_BURST = "TRAFFIC_BURST"
    SET_LED = "SET_LED"


class LedType(str, Enum):
    POWER = "power"
    ONLINE = "online"
    UPSTREAM = "upstream"
    LAN1 = "lan1"
    LAN2 = "lan2"
    LAN3 = "lan3"
    LAN4 = "lan4"
    SEND = "send"
    RECEIVE = "receive"


class ColorType(str, Enum):
    GREEN = "green"
    AMBER = "amber"
    RED = "red"
    OFF = "off"
    FLASH = "flash"
    FLASH_FAST = "flash_fast"


class LogLevel(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


class RouterCommandPayload(BaseModel):
    """Payload model for router command requests."""

    command: ActionType = Field(..., description="Operational control command keyword")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional command arguments")


class SetLedPayload(BaseModel):
    """Payload model for SET_LED command requests."""

    led: LedType = Field(..., description="Target chassis LED indicator")
    color: ColorType = Field(..., description="Target color state")


class RouterNodeMetadata(BaseModel):
    """Router node manifest metadata model."""

    id: str = Field(..., description="Unique router ID string")
    name: Optional[str] = Field(default=None, description="Human-readable router display name")
    url: str = Field(..., description="Target Cloud Run or local endpoint URL")
    location: Optional[str] = Field(default=None, description="Physical location description")
    purpose: Optional[str] = Field(default=None, description="Operational purpose description")
    manufacturer: Optional[str] = Field(default=None, description="Equipment manufacturer ID")
    model: Optional[str] = Field(default=None, description="Equipment model ID")
    source: Optional[str] = Field(default=None, description="Registration source (e.g. CLOUDRUN, MANUAL)")


class RouterLogEntry(BaseModel):
    """Structured hardware log entry model."""

    level: str = Field(default="INFO", description="Log severity level (e.g. INFO, WARN, ERROR)")
    message: str = Field(..., description="Hardware action or status log message")
    timestamp: str = Field(..., description="Formatted UTC timestamp string")
    timestamp_epoch: Optional[float] = Field(default=None, description="POSIX epoch timestamp")
    timestamp_iso: Optional[str] = Field(default=None, description="ISO 8601 timestamp string")


class RouterTelemetry(BaseModel):
    """Router operational telemetry model."""

    booting: bool = Field(default=False, description="System POST boot state flag")
    fail_mode: bool = Field(default=False, description="BGP fault injection state flag")
    last_command: str = Field(default="N/A", description="Last executed hardware command")
    status: str = Field(default="OPERATIONAL", description="Current operational status")
    uptime_seconds: int = Field(default=0, description="System uptime in seconds")


class RouterStatusResponse(BaseModel):
    """Complete status and telemetry response model."""

    metadata: Dict[str, Any] = Field(..., description="Router identification metadata")
    telemetry: RouterTelemetry = Field(..., description="Operational telemetry object")
    leds: Dict[str, str] = Field(..., description="Current chassis LED color state map")
    logs: Optional[List[RouterLogEntry]] = Field(default=None, description="Recent log entries")


class FleetSummaryItem(BaseModel):
    """Condensed telemetry status summary model for a single router node in a fleet query batch."""

    router_id: str = Field(..., description="Router node unique string ID")
    name: Optional[str] = Field(default=None, description="Router display name")
    status: str = Field(default="UNKNOWN", description="Operational status (e.g. OPERATIONAL, FAULT)")
    telemetry: Optional[Dict[str, Any]] = Field(default=None, description="Condensed telemetry summary object")
    leds: Optional[Dict[str, str]] = Field(default=None, description="Current chassis LED indicators map")
    error: Optional[str] = Field(default=None, description="Error message if querying node status failed")


class FleetSummaryResponse(BaseModel):
    """Paginated fleet summary status response model."""

    total_count: int = Field(..., description="Total count of routers registered in the fleet")
    page_size: int = Field(..., description="Number of items returned in this page batch")
    next_page_token: Optional[str] = Field(default=None, description="Cursor token for fetching the next page (None if end of list)")
    routers: List[FleetSummaryItem] = Field(..., description="List of router status summaries for the current page batch")

