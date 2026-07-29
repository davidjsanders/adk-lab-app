#!/usr/bin/env python3
"""SysMan Model Context Protocol (MCP) Server.

Provides FastMCP tools to query system statuses, retrieve logs,
execute configuration and lifecycle controls, and render interactive
A2UI cards for simulated Linux hosts, Jira app servers, and Confluence nodes.
"""

import logging
import os
import sys
from typing import Any, Dict, List
from dotenv import load_dotenv
from fastmcp import FastMCP

from classes import EmulatorClient, CardBuilder
from models import SystemMetadata, SystemStatus, LogEntry

# Load environment configuration
load_dotenv()

# Configure structured logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sysman-mcp-server")

mcp = FastMCP("SysMan Operations MCP Server")
client = EmulatorClient()


@mcp.tool()
def list_systems() -> List[SystemMetadata]:
    """Lists all registered virtual systems in the fleet.

    Returns:
        List of SystemMetadata models containing system details.
    """
    return client.list_systems()


@mcp.tool()
def get_system_status(system_id: str) -> SystemStatus:
    """Queries detailed status, metrics, and health of a specific system.

    Args:
        system_id: Unique string ID of the target system (e.g. 'linux-server-01').

    Returns:
        SystemStatus model containing telemetry metrics, logs and actions.
    """
    return client.get_system_status(system_id)


@mcp.tool()
def execute_system_command(system_id: str, command: str) -> Dict[str, Any]:
    """Sends lifecycle restarts, Garbage Collection, websocket reconnects or fault injections.

    Args:
        system_id: Target system ID.
        command: Command keyword to execute.
          Valid values:
            - For Linux: 'REBOOT', 'STOP_NODE_EXPORTER', 'START_NODE_EXPORTER', 'INJECT_FAULT', 'CLEAR_FAULT'
            - For Jira: 'RESTART_JIRA', 'GC_CLEANUP', 'EXPAND_DB_POOL', 'EXHAUST_DB_POOL', 'TRIGGER_JVM_LEAK', 'RESET_SIMULATION'
            - For Confluence: 'REBOOT', 'RECONNECT_WEBSOCKETS', 'PURGE_ATTACHMENTS', 'DROP_WEBSOCKETS', 'FILL_DISK', 'RESET_SIMULATION'

    Returns:
        Dictionary containing execution result status and message.
    """
    return client.execute_system_command(system_id, command)


@mcp.tool()
def get_system_logs(system_id: str, limit: int = 15) -> List[LogEntry]:
    """Retrieves recent syslog or application logs for the requested system.

    Args:
        system_id: Target system ID.
        limit: Number of recent log lines to retrieve (default: 15).

    Returns:
        List of LogEntry models containing level, timestamp and log message.
    """
    return client.get_system_logs(system_id, limit=limit)


@mcp.tool()
def render_system_card(system_id: str) -> str:
    """Renders a native A2UI v0.8 interactive system operations status card.

    Args:
        system_id: Unique string ID of target system.

    Returns:
        A2UI v0.8 JSON declarative card payload string enclosed in <a2ui-json> tags.
    """
    import json
    import time
    surface_id = f"sysman_card_{system_id.lower().replace('-', '_')}_{int(time.time()*1000)}"
    try:
        status = client.get_system_status(system_id)
        
        builder = CardBuilder(status, surface_id)
        components = builder.build()
        payload = [
            {
                "version": "v0.8",
                "beginRendering": {
                    "surfaceId": surface_id,
                    "root": "card-root"
                }
            },
            {
                "version": "v0.8",
                "surfaceUpdate": {
                    "surfaceId": surface_id,
                    "components": components
                }
            }
        ]
        return f"<a2ui-json>\n{json.dumps(payload, indent=2)}\n</a2ui-json>"

    except Exception as err:
        logger.error(f"Failed rendering system card: {err}")
        raise RuntimeError(f"Failed rendering system card for {system_id}") from err


@mcp.tool()
def render_system_logs_card(system_id: str) -> str:
    """Renders a native A2UI v0.8 interactive diagnostics logs card for the target system.

    Args:
        system_id: Unique string ID of target system.

    Returns:
        A2UI v0.8 JSON declarative logs card payload string enclosed in <a2ui-json> tags.
    """
    import json
    import time
    surface_id = f"sysman_logs_{system_id.lower().replace('-', '_')}_{int(time.time()*1000)}"
    try:
        status = client.get_system_status(system_id)
        
        builder = CardBuilder(status, surface_id)
        components = builder.build_logs_card()
        payload = [
            {
                "version": "v0.8",
                "beginRendering": {
                    "surfaceId": surface_id,
                    "root": "logs-card-root"
                }
            },
            {
                "version": "v0.8",
                "surfaceUpdate": {
                    "surfaceId": surface_id,
                    "components": components
                }
            }
        ]
        return f"<a2ui-json>\n{json.dumps(payload, indent=2)}\n</a2ui-json>"

    except Exception as err:
        logger.error(f"Failed rendering system logs card: {err}")
        raise RuntimeError(f"Failed rendering system logs card for {system_id}") from err


# Expose ASGI HTTP application instance for server execution
app = mcp.http_app(transport="streamable-http", stateless_http=True)


if __name__ == "__main__":
    transport = "stdio" if "--stdio" in sys.argv else "streamable-http"
    try:
        if transport == "stdio":
            mcp.run(transport=transport)
        else:
            port = int(os.getenv("PORT", "8002"))
            mcp.run(transport=transport, host="0.0.0.0", port=port)
    except (KeyboardInterrupt, SystemExit):
        logger.info("FastMCP server shut down cleanly.")
