#!/usr/bin/env python3
"""Router Fleet Operations Model Context Protocol (MCP) Server.

Provides FastMCP tools for AI agents to query fleet telemetry, dispatch hardware control commands,
fetch operations logs, run SNMP MIB walks, and render snapshot A2UI cards for router nodes.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from fastmcp import FastMCP

from classes import build_a2ui_router_card_manifest
from helpers import (
    ActionType,
    ColorType,
    LedType,
    LogLevel,
    dispatch_command,
    dispatch_fetch_logs,
    dispatch_set_led,
    dispatch_snmp_walk,
    fetch_fleet_data,
    fetch_fleet_summary,
    fetch_status_data,
    setup_json_logging,
)

# Load environment configuration from .env file (prioritizing local workspace settings)
load_dotenv(override=True)

# Configure structured Cloud Run JSON logging
logger = setup_json_logging("router-mcp-server")

# Initialize FastMCP Server
mcp = FastMCP("Router Fleet Operations MCP Server")

DEFAULT_DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://router-dashboard-cta6n7hkya-uc.a.run.app")


@mcp.tool()
def list_router_fleet() -> List[Dict[str, Any]]:
    """Lists all registered router nodes in the fleet from the operations dashboard.

    Args:
        None.

    Returns:
        List of router node metadata dictionaries (id, name, location, state, url, etc.).

    Raises:
        RuntimeError: If communicating with dashboard service fails.
    """
    try:
        return fetch_fleet_data()
    except Exception as err:
        logger.error(f"Failed querying router fleet: {err}")
        raise RuntimeError(f"Failed querying router fleet at {DEFAULT_DASHBOARD_URL}/api/routers: {err}")


@mcp.tool()
def get_fleet_summary(
    page_size: int = 10,
    page_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetches status telemetry summaries across fleet router nodes in parallel with cursor-based pagination.

    Args:
        page_size: Maximum number of router node summaries to return per page batch (default: 10, max: 50).
        page_token: Optional cursor string token for fetching the next page (omit for first page).

    Returns:
        Dictionary payload conforming to FleetSummaryResponse (total_count, page_size, next_page_token, routers).

    Raises:
        RuntimeError: If querying fleet registry fails.
    """
    try:
        return fetch_fleet_summary(page_size=page_size, page_token=page_token)
    except Exception as err:
        logger.error(f"Failed querying fleet summary: {err}")
        raise RuntimeError(f"Failed querying fleet summary: {err}")



@mcp.tool()
def get_router_status(router_id: str) -> Dict[str, Any]:
    """Fetches full state telemetry, LED colors, uptime, and state directly from a targeted router node.

    Args:
        router_id: Unique string ID of target router node (e.g. 'CAN-NN2-CENTRAL-01').

    Returns:
        Dictionary containing router state, uptime_seconds, leds map, and metadata.

    Raises:
        RuntimeError: If status query fails.
    """
    try:
        return fetch_status_data(router_id)
    except Exception as err:
        logger.error(f"Failed fetching status directly for '{router_id}': {err}")
        raise RuntimeError(f"Failed fetching status for '{router_id}': {err}")


@mcp.tool()
def render_router_card(router_id: str) -> str:
    """Renders a compact A2UI v0.8 snapshot card for the target router node.

    Args:
        router_id: Unique string ID of target router node (e.g. 'CAN-NN2-CENTRAL-01').

    Returns:
        A2UI v0.8 JSON declarative card payload string enclosed in <a2ui-json> tags.

    Raises:
        RuntimeError: If status query for card payload fails.
    """
    status_data = fetch_status_data(router_id)
    return build_a2ui_router_card_manifest(status_data, default_id=router_id)


@mcp.tool()
def set_router_led(router_id: str, led: LedType, color: ColorType) -> Dict[str, Any]:
    """Sets a specific LED indicator light color on a router chassis (e.g. power='green', upstream='red').

    Args:
        router_id: Target router node ID string.
        led: Chassis LED indicator ('power', 'online', 'upstream', 'lan1', 'lan2', 'lan3', 'lan4', 'send', 'receive').
        color: Target color state ('green', 'amber', 'red', 'off', 'flash', 'flash_fast').

    Returns:
        Dictionary containing command execution result and updated LED chassis state.

    Raises:
        RuntimeError: If setting LED status fails.
    """
    return dispatch_set_led(router_id, led, color)


@mcp.tool()
def reboot_router(router_id: str) -> Dict[str, Any]:
    """Initiates a system reboot sequence (POST diagnostic reboot) on a router node.

    Args:
        router_id: Target router node ID string.

    Returns:
        Dictionary containing execution result and system state.

    Raises:
        RuntimeError: If dispatching reboot command fails.
    """
    return dispatch_command(router_id, "REBOOT")


@mcp.tool()
def inject_bgp_fault(router_id: str) -> Dict[str, Any]:
    """Injects an immediate BGP upstream peering fault on a router node for failure testing.

    Args:
        router_id: Target router node ID string.

    Returns:
        Dictionary containing execution result and fault state.

    Raises:
        RuntimeError: If dispatching fault injection command fails.
    """
    return dispatch_command(router_id, "BGP_FAULT")


@mcp.tool()
def reset_bgp_session(router_id: str) -> Dict[str, Any]:
    """Restores BGP peering session state and clears active fail mode on a router node.

    Args:
        router_id: Target router node ID string.

    Returns:
        Dictionary containing execution result and restored operational state.

    Raises:
        RuntimeError: If dispatching BGP reset command fails.
    """
    return dispatch_command(router_id, "BGP_RESET")


@mcp.tool()
def send_router_command(
    router_id: str,
    action: ActionType,
    parameters: Optional[Union[Dict[str, Any], str]] = None,
) -> Dict[str, Any]:
    """Dispatches generic control commands directly to a router node.

    Args:
        router_id: Unique string ID of target router node.
        action: Operational command ('POWER_UP', 'POWER_DOWN', 'REBOOT', 'BGP_RESET', 'BGP_FAULT', 'TRAFFIC_BURST', 'SET_LED').
        parameters: Optional parameters dictionary or string payload.

    Returns:
        Dictionary containing execution status, output message, and resulting state.

    Raises:
        RuntimeError: If command dispatch fails.
    """
    return dispatch_command(router_id, action, parameters)


@mcp.tool()
def fetch_router_logs(
    router_id: str, seconds: int = 300, level: Optional[LogLevel] = None
) -> List[Dict[str, Any]]:
    """Fetches collected historical hardware action log entries directly from a router node.

    Args:
        router_id: Unique string ID of target router node.
        seconds: Time window in seconds (default: 300s).
        level: Filter severity level ('INFO', 'WARN', 'ERROR').

    Returns:
        List of historical hardware action log entry dictionaries.

    Raises:
        RuntimeError: If log retrieval fails.
    """
    return dispatch_fetch_logs(router_id, seconds, level)


@mcp.tool()
def run_snmp_walk(router_id: str, oid: str = ".1.3.6.1") -> Dict[str, Any]:
    """Executes an SNMP MIB tree query walk directly on a target router node.

    Args:
        router_id: Unique string ID of target router node.
        oid: Root Object Identifier to query (default: '.1.3.6.1').

    Returns:
        Dictionary containing SNMP response status, matched variables, and formatted MIB output.

    Raises:
        RuntimeError: If SNMP walk query fails.
    """
    return dispatch_snmp_walk(router_id, oid)


if __name__ == "__main__":
    import sys
    # Default to streamable-http on port 8000 for MCP Inspector UI connectivity
    transport = "stdio" if "--stdio" in sys.argv else "streamable-http"
    try:
        mcp.run(transport=transport, host="127.0.0.1", port=8000)
    except (KeyboardInterrupt, SystemExit):
        logger.info("FastMCP server shut down cleanly.")

