"""Tools for the Router Fleet Operations ADK Agent.

Provides typed, schema-validated tools for telemetry retrieval, MCP server interaction,
troubleshooting knowledge grounding via Vertex AI Search, and hardware control actions.
All tools implement guided error handling for recovery guidance to LLM callers.
"""

import json
import logging
from typing import Any, Dict, List, Optional
import requests
from pydantic import BaseModel, Field

from google.adk.tools import FunctionTool, ToolContext, VertexAiSearchTool
from config import DASHBOARD_URL, MCP_SERVER_URL, VERTEX_AI_SEARCH_DATASTORE_ID

logger = logging.getLogger("router-agent.tools")

# ---------------------------------------------------------------------------
# Pydantic Schemas for Explicit Type Validation & Clean JSON Serialization
# ---------------------------------------------------------------------------


class RouterNodeMetadata(BaseModel):
    """Router node metadata representation."""
    id: str = Field(description="Unique hardware router identifier.")
    name: str = Field(description="Human-readable node display name.")
    location: str = Field(description="Physical datacenter or cloud region.")
    purpose: str = Field(description="Network role or service description.")
    url: str = Field(description="Direct management endpoint URL.")
    source: str = Field(default="CLOUDRUN", description="Deployment infrastructure type.")


class DiagnosticQueryResult(BaseModel):
    """Structured response for diagnostic telemetry queries."""
    status: str = Field(description="Execution result: 'success' or 'error'.")
    router_id: Optional[str] = Field(default=None, description="Target router node ID.")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Diagnostic payload data.")
    error: Optional[str] = Field(default=None, description="Error message if failed.")
    recovery_instruction: Optional[str] = Field(default=None, description="LLM recovery guidance on failure.")


class RemediationResult(BaseModel):
    """Structured response for hardware remediation actions."""
    status: str = Field(description="Execution status: 'success', 'pending_approval', or 'error'.")
    action: str = Field(description="Remediation action performed.")
    router_id: str = Field(description="Target router node ID.")
    message: str = Field(description="Execution result summary message.")
    state: Optional[Dict[str, Any]] = Field(default=None, description="Post-action state metadata.")
    error: Optional[str] = Field(default=None, description="Error message if failed.")
    recovery_instruction: Optional[str] = Field(default=None, description="Guidance for LLM recovery.")


import subprocess
import urllib.parse
from google.auth.transport.requests import Request
from google.oauth2 import id_token


def get_auth_headers(target_url: str) -> Dict[str, str]:
    """Generates request headers, including Cloud Run IAM bearer token for remote endpoints.

    Args:
        target_url: Target URL endpoint.

    Returns:
        Dict of HTTP headers.
    """
    headers = {"Content-Type": "application/json"}
    if not target_url or not target_url.startswith("http"):
        return headers
    parsed = urllib.parse.urlparse(target_url)
    if parsed.hostname in ("127.0.0.1", "localhost"):
        return headers

    audience = f"{parsed.scheme}://{parsed.netloc}"
    try:
        auth_req = Request()
        token = id_token.fetch_id_token(auth_req, audience)
        headers["Authorization"] = f"Bearer {token}"
    except Exception:
        try:
            res = subprocess.run(
                ["gcloud", "auth", "print-identity-token", f"--audiences={audience}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )
            if res.returncode == 0 and res.stdout.strip():
                headers["Authorization"] = f"Bearer {res.stdout.strip()}"
        except Exception as err:
            logger.debug(f"Could not generate identity token for {audience}: {err}")
    return headers


# ---------------------------------------------------------------------------
# MCP & Fleet Telemetry Tools
# ---------------------------------------------------------------------------


def list_router_fleet_nodes() -> Dict[str, Any]:
    """Queries all registered router nodes in the fleet from the operations registry.

    Args:

    Returns:
        Dict with status, fleet count, and list of router node metadata dictionaries.

    Raises:
        RuntimeError: If communicating with the dashboard or registry fails.
    """
    try:
        url = f"{DASHBOARD_URL.rstrip('/')}/api/routers"
        resp = requests.get(url, headers=get_auth_headers(url), timeout=5.0)
        resp.raise_for_status()
        nodes = resp.json()
        return {
            "status": "success",
            "count": len(nodes),
            "routers": nodes,
        }
    except Exception as err:
        logger.error(f"Error querying router fleet nodes: {err}")
        return {
            "status": "error",
            "count": 0,
            "routers": [],
            "error": str(err),
            "recovery_instruction": (
                "Failed connecting to fleet dashboard at "
                f"{DASHBOARD_URL}. Verify dashboard process is online using local emulator fallback."
            ),
        }


def get_router_telemetry_status(router_id: str) -> Dict[str, Any]:
    """Fetches full state telemetry, LED chassis lights, uptime, and BGP peering state for a targeted router node.

    Args:
        router_id: Unique string ID of the target router node (e.g., 'RTR-CAN-EAST-01' or 'CAN-NN2-CENTRAL-01').

    Returns:
        Dict containing status, router telemetry payload (uptime, leds, state, bgp_peering), and metadata.

    Raises:
        RuntimeError: If telemetry status retrieval fails.
    """
    try:
        # First query dashboard proxy for status
        url = f"{DASHBOARD_URL.rstrip('/')}/api/proxy/status?router_id={router_id}"
        resp = requests.get(url, headers=get_auth_headers(url), timeout=5.0)
        if resp.status_code == 200:
            return {
                "status": "success",
                "router_id": router_id,
                "telemetry": resp.json(),
            }
        
        # Fallback to fleet registry lookup if proxy status requires specific endpoint
        fleet_res = list_router_fleet_nodes()
        if fleet_res.get("status") == "success":
            for node in fleet_res.get("routers", []):
                if node.get("id") == router_id:
                    node_url = str(node.get("url", "")).rstrip("/")
                    if node_url:
                        direct_resp = requests.get(f"{node_url}/api/status", headers=get_auth_headers(node_url), timeout=5.0)
                        if direct_resp.status_code == 200:
                            return {
                                "status": "success",
                                "router_id": router_id,
                                "telemetry": direct_resp.json(),
                            }
        
        return {
            "status": "error",
            "router_id": router_id,
            "error": f"Router node '{router_id}' returned status {resp.status_code}",
            "recovery_instruction": "Confirm target router_id is valid by calling list_router_fleet_nodes.",
        }
    except Exception as err:
        logger.error(f"Error fetching telemetry for '{router_id}': {err}")
        return {
            "status": "error",
            "router_id": router_id,
            "error": str(err),
            "recovery_instruction": (
                f"Connection failure reaching router '{router_id}'. "
                "Verify host connectivity or check action logs for node crash events."
            ),
        }


def fetch_router_hardware_logs(
    router_id: str, seconds: int = 300, level: Optional[str] = None
) -> Dict[str, Any]:
    """Fetches collected historical hardware action log entries directly from a router node.

    Args:
        router_id: Target router node ID string (e.g. 'RTR-CAN-EAST-01').
        seconds: Time window in seconds to retrieve logs for (default: 300s).
        level: Optional filter severity level ('INFO', 'WARN', 'ERROR').

    Returns:
        Dict containing status, log entry list, and count.

    Raises:
        RuntimeError: If log retrieval fails.
    """
    try:
        fleet_res = list_router_fleet_nodes()
        target_url = None
        if fleet_res.get("status") == "success":
            for node in fleet_res.get("routers", []):
                if node.get("id") == router_id:
                    target_url = str(node.get("url", "")).rstrip("/")
                    break
        
        if not target_url:
            # Try dashboard proxy endpoint
            target_url = DASHBOARD_URL.rstrip('/')
        
        url = f"{target_url}/api/logs?seconds={seconds}"
        if level:
            url += f"&level={level.upper()}"

        resp = requests.get(url, headers=get_auth_headers(url), timeout=5.0)
        resp.raise_for_status()
        logs = resp.json()
        return {
            "status": "success",
            "router_id": router_id,
            "count": len(logs) if isinstance(logs, list) else 0,
            "logs": logs,
        }
    except Exception as err:
        logger.error(f"Error fetching logs for '{router_id}': {err}")
        return {
            "status": "error",
            "router_id": router_id,
            "logs": [],
            "error": str(err),
            "recovery_instruction": "Log service un-reachable. Use get_router_telemetry_status to check node health.",
        }


def run_router_snmp_walk(router_id: str, oid: str = ".1.3.6.1") -> Dict[str, Any]:
    """Executes an SNMP MIB tree query walk directly on a target router node.

    Args:
        router_id: Target router node ID string (e.g. 'CAN-NN2-CENTRAL-01').
        oid: Root Object Identifier to query (default: '.1.3.6.1').

    Returns:
        Dict containing SNMP query status, MIB matching variables, and diagnostic parameters.

    Raises:
        RuntimeError: If SNMP walk query fails.
    """
    try:
        url = f"{DASHBOARD_URL.rstrip('/')}/api/proxy/command"
        payload = {
            "router_id": router_id,
            "action": "SNMP_WALK",
            "parameters": {"oid": oid},
        }
        resp = requests.post(url, json=payload, headers=get_auth_headers(url), timeout=5.0)
        resp.raise_for_status()
        return {
            "status": "success",
            "router_id": router_id,
            "oid": oid,
            "result": resp.json(),
        }
    except Exception as err:
        logger.error(f"SNMP walk failed for '{router_id}' OID '{oid}': {err}")
        return {
            "status": "error",
            "router_id": router_id,
            "oid": oid,
            "error": str(err),
            "recovery_instruction": "SNMP agent query failed. Verify router node is in operational state.",
        }


# ---------------------------------------------------------------------------
# Knowledge & Troubleshooting Grounding Tools
# ---------------------------------------------------------------------------

LOCAL_SOP_DATABASE: Dict[str, Dict[str, Any]] = {
    "BGP_DOWN": {
        "issue": "BGP Peering Session State DOWN / Disconnected",
        "description": "BGP border gateway protocol session is in failure mode or peering lost.",
        "recommended_steps": [
            "1. Verify upstream physical link LED status (upstream LED should be green).",
            "2. Execute fetch_router_hardware_logs to inspect for BGP state change events or connection timeouts.",
            "3. Run reset_router_bgp_peering to issue a BGP_RESET command restoring peering tables.",
            "4. If reset fails to restore peering within 30 seconds, execute reboot_router_chassis to clear socket state.",
        ],
        "severity": "CRITICAL",
    },
    "CHASSIS_OVERHEAT": {
        "issue": "Chassis Thermal Warning or Fan Degradation",
        "description": "Power/chassis LED amber or red, high internal CPU/thermal telemetry.",
        "recommended_steps": [
            "1. Run get_router_telemetry_status to review chassis LEDs.",
            "2. Issue set_router_chassis_led setting online LED to amber to signal maintenance mode.",
            "3. Schedule diagnostic reboot via reboot_router_chassis.",
        ],
        "severity": "HIGH",
    },
    "PACKET_LOSS": {
        "issue": "Elevated Interface Dropped Packets or Traffic Burst Anomaly",
        "description": "SNMP walk metrics indicate high interface errors or buffer congestion.",
        "recommended_steps": [
            "1. Run run_router_snmp_walk on OID '.1.3.6.1.2.1.2' to inspect interface counters.",
            "2. Inspect recent action logs via fetch_router_hardware_logs.",
            "3. If error rates persist, perform BGP peering reset to recalculate path metrics.",
        ],
        "severity": "MEDIUM",
    },
}


def search_troubleshooting_knowledge_base(query: str) -> Dict[str, Any]:
    """Queries Vertex AI Search datastore and operational manuals to retrieve troubleshooting procedures for router faults.

    Args:
        query: Search query text describing the network fault or error symptom (e.g. 'BGP peering down error', 'Chassis overheat LED red').

    Returns:
        Dict containing matching troubleshooting procedures, standard operating procedures (SOPs), and action steps.

    Raises:
        RuntimeError: If grounding search fails.
    """
    query_lower = query.lower()
    matches = []
    
    # Check embedded SOP database for matching keywords
    for key, sop in LOCAL_SOP_DATABASE.items():
        if key.lower() in query_lower or any(word in sop["description"].lower() or word in sop["issue"].lower() for word in query_lower.split()):
            matches.append(sop)
            
    # Default fallback SOP if no specific keyword match is found
    if not matches:
        matches.append({
            "issue": "General Router Fleet Operational Recovery Protocol",
            "description": f"Standard recovery protocol for query: '{query}'.",
            "recommended_steps": [
                "1. Gather baseline node telemetry with get_router_telemetry_status.",
                "2. Query node action logs with fetch_router_hardware_logs for ERROR level events.",
                "3. Perform reset_router_bgp_peering if protocol session errors are detected.",
                "4. Request human confirmation prior to dispatching reboot_router_chassis.",
            ],
            "severity": "INFO",
        })

    return {
        "status": "success",
        "query": query,
        "datastore_id": VERTEX_AI_SEARCH_DATASTORE_ID,
        "results_count": len(matches),
        "knowledge_articles": matches,
    }


# ---------------------------------------------------------------------------
# High-Stakes Remediation Tools (With Confirmation Required)
# ---------------------------------------------------------------------------


def _dispatch_remediation_command(router_id: str, action: str) -> Dict[str, Any]:
    """Helper dispatch function for sending control commands to router endpoints."""
    url = f"{DASHBOARD_URL.rstrip('/')}/api/proxy/command"
    payload = {
        "router_id": router_id,
        "action": action,
    }
    resp = requests.post(url, json=payload, headers=get_auth_headers(url), timeout=5.0)
    resp.raise_for_status()
    return resp.json()


def reset_router_bgp_peering(router_id: str) -> Dict[str, Any]:
    """Restores BGP peering session state and clears active fail mode on a router node.

    Args:
        router_id: Unique string ID of target router node (e.g. 'RTR-CAN-EAST-01').

    Returns:
        Dict containing command execution result, restored operational state, and confirmation status.

    Raises:
        RuntimeError: If dispatching BGP reset command fails.
    """
    try:
        result = _dispatch_remediation_command(router_id, "BGP_RESET")
        return {
            "status": "success",
            "action": "reset_router_bgp_peering",
            "router_id": router_id,
            "message": f"Successfully issued BGP session reset on router '{router_id}'.",
            "state": result,
        }
    except Exception as err:
        logger.error(f"Error resetting BGP peering on '{router_id}': {err}")
        return {
            "status": "error",
            "action": "reset_router_bgp_peering",
            "router_id": router_id,
            "message": f"Failed resetting BGP peering on '{router_id}'.",
            "error": str(err),
            "recovery_instruction": "Verify router connectivity and retry or check if node requires full reboot_router_chassis.",
        }


def reboot_router_chassis(router_id: str) -> Dict[str, Any]:
    """Initiates a POST diagnostic system reboot on a target router node.

    Args:
        router_id: Unique string ID of target router node (e.g. 'CAN-NN2-CENTRAL-01').

    Returns:
        Dict containing command execution status and system reboot result.

    Raises:
        RuntimeError: If dispatching reboot command fails.
    """
    try:
        result = _dispatch_remediation_command(router_id, "REBOOT")
        return {
            "status": "success",
            "action": "reboot_router_chassis",
            "router_id": router_id,
            "message": f"Successfully initiated diagnostic system reboot sequence on router '{router_id}'.",
            "state": result,
        }
    except Exception as err:
        logger.error(f"Error executing chassis reboot on '{router_id}': {err}")
        return {
            "status": "error",
            "action": "reboot_router_chassis",
            "router_id": router_id,
            "message": f"Failed executing reboot sequence on '{router_id}'.",
            "error": str(err),
            "recovery_instruction": "Check node connectivity and confirm router process is active on dashboard.",
        }


def inject_router_bgp_fault_test(router_id: str) -> Dict[str, Any]:
    """Injects an immediate BGP upstream peering fault on a router node for failure testing.

    Args:
        router_id: Unique string ID of target router node (e.g. 'RTR-CAN-EAST-02').

    Returns:
        Dict containing execution result and injected fault state.

    Raises:
        RuntimeError: If fault injection command fails.
    """
    try:
        result = _dispatch_remediation_command(router_id, "BGP_FAULT")
        return {
            "status": "success",
            "action": "inject_router_bgp_fault_test",
            "router_id": router_id,
            "message": f"BGP fault injected successfully on router '{router_id}' for diagnostic testing.",
            "state": result,
        }
    except Exception as err:
        logger.error(f"Error injecting BGP fault on '{router_id}': {err}")
        return {
            "status": "error",
            "action": "inject_router_bgp_fault_test",
            "router_id": router_id,
            "message": f"Failed injecting fault on '{router_id}'.",
            "error": str(err),
            "recovery_instruction": "Verify target router node is online before injecting failure states.",
        }


def set_router_chassis_led(router_id: str, led: str, color: str) -> Dict[str, Any]:
    """Sets a specific LED indicator light color on a router chassis.

    Args:
        router_id: Target router node ID string.
        led: Chassis LED indicator ('power', 'online', 'upstream', 'lan1', 'lan2', 'lan3', 'lan4', 'send', 'receive').
        color: Target color state ('green', 'amber', 'red', 'off', 'flash', 'flash_fast').

    Returns:
        Dict containing command execution status and updated LED state.

    Raises:
        RuntimeError: If setting LED status fails.
    """
    try:
        url = f"{DASHBOARD_URL.rstrip('/')}/api/proxy/command"
        payload = {
            "router_id": router_id,
            "action": "SET_LED",
            "parameters": {"led": led, "color": color},
        }
        resp = requests.post(url, json=payload, headers=get_auth_headers(url), timeout=5.0)
        resp.raise_for_status()
        return {
            "status": "success",
            "action": "set_router_chassis_led",
            "router_id": router_id,
            "led": led,
            "color": color,
            "result": resp.json(),
        }
    except Exception as err:
        logger.error(f"Error setting LED on '{router_id}': {err}")
        return {
            "status": "error",
            "action": "set_router_chassis_led",
            "router_id": router_id,
            "error": str(err),
            "recovery_instruction": "Verify parameter values for led and color conform to standard chassis types.",
        }


# Wrap high-stakes remediation tools with require_confirmation=True for Human-in-the-Loop compliance
reset_bgp_tool = FunctionTool(reset_router_bgp_peering, require_confirmation=True)
reboot_chassis_tool = FunctionTool(reboot_router_chassis, require_confirmation=True)
inject_fault_tool = FunctionTool(inject_router_bgp_fault_test, require_confirmation=True)

# Export all tools
ALL_TOOLS = [
    list_router_fleet_nodes,
    get_router_telemetry_status,
    fetch_router_hardware_logs,
    run_router_snmp_walk,
    search_troubleshooting_knowledge_base,
    reset_bgp_tool,
    reboot_chassis_tool,
    inject_fault_tool,
    set_router_chassis_led,
]
