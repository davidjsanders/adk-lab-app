"""Helpers package for Router MCP Server."""

from .auth import (
    discover_iap_client_id,
    get_auth_headers,
    get_effective_control_password,
    get_oidc_id_token,
)
from .fleet import (
    dispatch_clone_router,
    dispatch_delete_router,
    dispatch_redeploy_routers,
    dispatch_register_router,
    fetch_fleet_data,
    fetch_status_data,
    get_router_node,
)
from .logger import CloudRunJsonFormatter, setup_json_logging
from .tools import (
    dispatch_command,
    dispatch_fetch_logs,
    dispatch_set_led,
    dispatch_snmp_walk,
    fetch_fleet_summary,
)
from .types import (
    ActionType,
    ColorType,
    FleetSummaryItem,
    FleetSummaryResponse,
    LedType,
    LogLevel,
    RouterCommandPayload,
    RouterLogEntry,
    RouterNodeMetadata,
    RouterStatusResponse,
    RouterTelemetry,
    SetLedPayload,
)

__all__ = [
    "CloudRunJsonFormatter",
    "setup_json_logging",
    "discover_iap_client_id",
    "get_oidc_id_token",
    "get_auth_headers",
    "get_effective_control_password",
    "fetch_fleet_data",
    "get_router_node",
    "fetch_status_data",
    "dispatch_clone_router",
    "dispatch_delete_router",
    "dispatch_redeploy_routers",
    "dispatch_register_router",
    "dispatch_command",
    "dispatch_set_led",
    "dispatch_fetch_logs",
    "dispatch_snmp_walk",
    "fetch_fleet_summary",
    "ActionType",
    "LedType",
    "ColorType",
    "LogLevel",
    "RouterCommandPayload",
    "SetLedPayload",
    "RouterLogEntry",
    "RouterTelemetry",
    "RouterStatusResponse",
    "RouterNodeMetadata",
    "FleetSummaryItem",
    "FleetSummaryResponse",
]
