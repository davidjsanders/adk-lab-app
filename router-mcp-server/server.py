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

from helpers import (
    ActionType,
    ColorType,
    LedType,
    LogLevel,
    dispatch_clone_router,
    dispatch_command,
    dispatch_delete_router,
    dispatch_fetch_logs,
    dispatch_redeploy_routers,
    dispatch_register_router,
    dispatch_set_led,
    dispatch_snmp_walk,
    fetch_a2ui_card_data,
    fetch_a2ui_image_card_data,
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
    """Renders a native interactive component-tree A2UI v0.8 snapshot card for the target router node.

    Use this tool when a standard interactive text & button component card is preferred.

    Args:
        router_id: Unique string ID of target router node (e.g. 'CAN-NN2-CENTRAL-01').

    Returns:
        A2UI v0.8 JSON declarative card payload string enclosed in <a2ui-json> tags.

    Raises:
        RuntimeError: If querying target router node for A2UI card fails.
    """
    try:
        return fetch_a2ui_card_data(router_id)
    except Exception as err:
        logger.error(f"Fetch of /a2compact for '{router_id}' failed: {err}")
        raise RuntimeError(f"Router '{router_id}' is unreachable or failed to provide A2UI card: {err}")



@mcp.tool()
def render_router_card_image(router_id: str) -> str:
    """Renders a high-fidelity visual PNG snapshot A2UI card for the target router node matching the Operations Console design.

    Use this tool when exact visual chassis formatting (glowing LED indicators, monospace telemetry grid, exact card styling) is required.

    Args:
        router_id: Unique string ID of target router node (e.g. 'CAN-NN2-CENTRAL-01').

    Returns:
        A2UI v0.8 JSON declarative card payload string containing an embedded Base64 PNG image enclosed in <a2ui-json> tags.

    Raises:
        RuntimeError: If querying target router node for PNG card fails.
    """
    try:
        return fetch_a2ui_image_card_data(router_id)
    except Exception as err:
        logger.error(f"Fetch of /a2image for '{router_id}' failed: {err}")
        raise RuntimeError(f"Failed rendering PNG card image for router '{router_id}': {err}")


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


@mcp.tool()
def clone_router(
    source_router_id: str,
    new_router_id: str,
    new_name: Optional[str] = None,
    location: Optional[str] = None,
    purpose: Optional[str] = None,
    deploy_cloud_run: Optional[bool] = None,
) -> Dict[str, Any]:
    """Clones an existing router configuration with customized parameter overrides and registers/deploys it.

    Args:
        source_router_id: Existing router node string ID to copy hardware specifications from (e.g. 'RTR-CAN-EAST-01').
        new_router_id: Unique string ID for the new cloned router instance (e.g. 'RTR-CAN-EAST-03').
        new_name: Optional custom display name (defaults to 'Copy of <source.name>').
        location: Optional physical datacenter or cloud location description.
        purpose: Optional operational gateway role description.
        deploy_cloud_run: Optional boolean flag to deploy a new GCP Cloud Run service (defaults to source setting).

    Returns:
        Dictionary containing operational status and registration metadata.

    Raises:
        RuntimeError: If source lookup or cloning operation fails.
    """
    return dispatch_clone_router(
        source_router_id=source_router_id,
        new_router_id=new_router_id,
        new_name=new_name,
        location=location,
        purpose=purpose,
        deploy_cloud_run=deploy_cloud_run,
    )


@mcp.tool()
def register_or_deploy_router(
    router_id: str,
    name: str,
    location: str,
    purpose: str = "Edge Core Router",
    deploy_cloud_run: bool = True,
    url: Optional[str] = None,
    control_password: Optional[str] = None,
) -> Dict[str, Any]:
    """Registers a new router node or provisions a brand new Cloud Run container service.

    Args:
        router_id: Unique string ID of new router node (e.g. 'RTR-US-WEST-01').
        name: Human-readable display name (e.g. 'Seattle BGP Border Gateway').
        location: Location string description (e.g. 'Seattle Datacenter, Rack 04').
        purpose: Operational role description.
        deploy_cloud_run: If True, deploys a container instance to Google Cloud Run (default: True).
        url: Optional endpoint URL (required if deploy_cloud_run is False).
        control_password: Optional control authorization secret (auto-generates UUID in Secret Manager if empty).

    Returns:
        Dictionary containing status and assigned endpoint URL.

    Raises:
        RuntimeError: If registration or deployment dispatch fails.
    """
    payload = {
        "id": router_id.strip(),
        "name": name.strip(),
        "location": location.strip(),
        "purpose": purpose.strip(),
        "deploy_cloud_run": deploy_cloud_run,
        "deploy_cloudrun": deploy_cloud_run,
        "url": url.strip() if url else "",
        "control_password": control_password.strip() if control_password else "",
        "control_header": "X-Control-Password",
    }
    return dispatch_register_router(payload)


@mcp.tool()
def delete_router_node(router_id: str) -> Dict[str, Any]:
    """Tears down a router node (deletes its Cloud Run container service, Secret Manager key, and registry entry).

    Args:
        router_id: Unique string ID of target router node (e.g. 'RTR-CAN-ATLANTIC-02').

    Returns:
        Dictionary containing teardown result and status message.

    Raises:
        RuntimeError: If teardown request fails.
    """
    return dispatch_delete_router(router_id)


@mcp.tool()
def redeploy_router_node(router_ids: Union[List[str], str]) -> Dict[str, Any]:
    """Triggers an immediate container redeployment on Cloud Run for target router node(s).

    Args:
        router_ids: Single string ID or list of string IDs of target Cloud Run router nodes.

    Returns:
        Dictionary containing operational status and redeployment summary results per node.

    Raises:
        RuntimeError: If redeployment dispatch fails.
    """
    ids_list = [router_ids] if isinstance(router_ids, str) else router_ids
    return dispatch_redeploy_routers(ids_list)
# Expose ASGI application instance for Gunicorn / Uvicorn server execution on Cloud Run
app = mcp.http_app(transport="streamable-http", stateless_http=True)


if __name__ == "__main__":
    import sys
    # Default to streamable-http on port 8000 for MCP Inspector UI connectivity
    transport = "stdio" if "--stdio" in sys.argv else "streamable-http"
    try:
        mcp.run(transport=transport, host="127.0.0.1", port=8000)
    except (KeyboardInterrupt, SystemExit):
        logger.info("FastMCP server shut down cleanly.")

