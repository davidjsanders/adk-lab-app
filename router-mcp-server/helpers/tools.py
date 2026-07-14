"""Tool execution logic and HTTP dispatching implementations."""

import ast
import json
import logging
from typing import Any, Dict, List, Optional, Union
import urllib.parse

import requests

from .auth import get_auth_headers, get_effective_control_password
from .fleet import fetch_fleet_data, get_router_node
from .logger import setup_json_logging
from .types import ActionType, ColorType, FleetSummaryItem, FleetSummaryResponse, LedType, LogLevel, SetLedPayload

logger = setup_json_logging("router-mcp-server.tools")


def _normalize_set_led_params(params: Dict[str, Any]) -> SetLedPayload:
    """Normalizes raw input LED parameters into a validated SetLedPayload Pydantic model.

    Args:
        params: Dictionary containing raw LED name and color key-value arguments.

    Returns:
        Validated SetLedPayload Pydantic model instance.

    Raises:
        ValueError: If LED or color values cannot be validated against allowed Enums.
    """
    raw = dict(params)
    if "state" in raw and "color" not in raw:
        raw["color"] = raw.pop("state")
    if "led_name" in raw and "led" not in raw:
        raw["led"] = raw.pop("led_name")

    led_val = str(raw.get("led", "")).lower().strip()
    led_alias_map = {
        "pwr": "power", "power_led": "power", "pwr_led": "power",
        "recv": "receive", "rx": "receive", "tx": "send",
        "wan": "upstream", "internet": "upstream", "link": "online",
    }
    norm_led = led_alias_map.get(led_val, led_val)

    color_val = str(raw.get("color", "")).lower().strip()
    color_alias_map = {
        "on": "green", "ok": "green", "active": "green", "enabled": "green",
        "yellow": "amber", "orange": "amber", "warning": "amber",
        "error": "red", "fault": "red", "critical": "red",
        "blink": "flash", "blinking": "flash", "flashing": "flash",
        "disabled": "off",
    }
    norm_color = color_alias_map.get(color_val, color_val)

    return SetLedPayload(led=LedType(norm_led), color=ColorType(norm_color))


def dispatch_command(
    router_id: str,
    action: Union[ActionType, str],
    parameters: Optional[Union[Dict[str, Any], str]] = None,
) -> Dict[str, Any]:
    """Dispatches an operational command payload directly to a targeted router node endpoint.

    Args:
        router_id: Unique string ID of target router node.
        action: Operational command keyword string or ActionType Enum value.
        parameters: Optional dictionary or JSON string of command arguments.

    Returns:
        Dictionary containing command execution status, output message, and resulting state.

    Raises:
        RuntimeError: If target router URL resolution or HTTP execution fails.
    """
    node = get_router_node(router_id)
    base_url = str(node.get("url", "")).rstrip("/")
    if not base_url:
        raise RuntimeError(f"Router node '{router_id}' has no configured target URL.")

    action_str = action.value if isinstance(action, ActionType) else str(action)
    url = f"{base_url}/api/command"
    headers = get_auth_headers(url)
    control_header = node.get("control_header", "X-Control-Password")
    control_pass = get_effective_control_password(node)
    headers[control_header] = control_pass

    params_dict: Dict[str, Any] = {}
    if isinstance(parameters, str) and parameters.strip():
        try:
            params_dict = json.loads(parameters)
        except Exception:
            try:
                params_dict = ast.literal_eval(parameters)
            except Exception as err:
                logger.warning(f"Failed parsing string parameters '{parameters}': {err}")
    elif isinstance(parameters, dict):
        params_dict = dict(parameters)

    match action_str.upper().strip():
        case "SET_LED":
            if params_dict:
                try:
                    set_led_model = _normalize_set_led_params(params_dict)
                    params_dict = set_led_model.model_dump()
                except Exception as val_err:
                    logger.debug(f"Pydantic SET_LED normalization note: {val_err}")
        case "POWER_UP" | "POWER_DOWN" | "REBOOT" | "BGP_RESET" | "BGP_FAULT" | "TRAFFIC_BURST":
            pass
        case custom_action:
            logger.info(f"Dispatching custom hardware action '{custom_action}'")

    payload = {"command": action_str, "parameters": params_dict}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 400:
            logger.warning(f"Router returned HTTP 400 for command '{action_str}': {resp.text}")
            try:
                return resp.json()
            except Exception:
                return {"status": "ERROR", "error": "Bad Request", "message": resp.text}
        resp.raise_for_status()
        return resp.json()
    except Exception as err:
        logger.error(f"Failed dispatching command '{action_str}' directly to '{router_id}': {err}")
        raise RuntimeError(f"Failed dispatching command '{action_str}' directly to '{router_id}': {err}")


def dispatch_set_led(
    router_id: str,
    led: Union[LedType, str],
    color: Union[ColorType, str],
) -> Dict[str, Any]:
    """Helper tool for setting a specific router chassis LED state directly using Pydantic models.

    Args:
        router_id: Unique string ID of target router node.
        led: Chassis LED indicator string or LedType Enum.
        color: Target color state string or ColorType Enum.

    Returns:
        Dictionary containing command execution result and updated LED chassis state.

    Raises:
        RuntimeError: If setting LED status fails.
        ValueError: If provided LED name or color is invalid.
    """
    norm_led = led if isinstance(led, LedType) else LedType(str(led).lower().strip())
    norm_color = color if isinstance(color, ColorType) else ColorType(str(color).lower().strip())
    payload = SetLedPayload(led=norm_led, color=norm_color)
    return dispatch_command(router_id, "SET_LED", payload.model_dump())


def dispatch_fetch_logs(
    router_id: str, seconds: int = 300, level: Optional[Union[LogLevel, str]] = None
) -> List[Dict[str, Any]]:
    """Fetches collected historical hardware action log entries directly from a target router node.

    Args:
        router_id: Unique string ID of target router node.
        seconds: Elapsed time window cutoff in seconds (default: 300).
        level: Optional log severity level filter string or LogLevel Enum.

    Returns:
        List of historical hardware action log entry dictionaries.

    Raises:
        RuntimeError: If target URL resolution or HTTP log retrieval fails.
    """
    node = get_router_node(router_id)
    base_url = str(node.get("url", "")).rstrip("/")
    if not base_url:
        raise RuntimeError(f"Router node '{router_id}' has no configured target URL.")

    url = f"{base_url}/api/logs?seconds={seconds}"
    if level:
        level_str = level.value if isinstance(level, LogLevel) else str(level)
        url += f"&level={level_str}"
    headers = get_auth_headers(url)
    control_header = node.get("control_header", "X-Control-Password")
    control_pass = get_effective_control_password(node)
    headers[control_header] = control_pass

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            return data.get("logs", [])
        return data if isinstance(data, list) else []
    except Exception as err:
        logger.error(f"Failed fetching logs directly for '{router_id}': {err}")
        raise RuntimeError(f"Failed fetching logs directly for '{router_id}': {err}")


def dispatch_snmp_walk(router_id: str, oid: str = ".1.3.6.1") -> Dict[str, Any]:
    """Executes an SNMP MIB tree query walk directly on a target router node.

    Args:
        router_id: Unique string ID of target router node.
        oid: Root Object Identifier to query (default: '.1.3.6.1' MIB-II tree).

    Returns:
        Dictionary containing SNMP response status, matched variables, and formatted MIB output.

    Raises:
        RuntimeError: If SNMP walk query fails.
    """
    node = get_router_node(router_id)
    base_url = str(node.get("url", "")).rstrip("/")
    if not base_url:
        raise RuntimeError(f"Router node '{router_id}' has no configured target URL.")

    params = f"oid={urllib.parse.quote(oid)}&format=json"
    url = f"{base_url}/snmp/walk?{params}"
    headers = get_auth_headers(url)

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as err:
        logger.error(f"Failed executing SNMP walk directly on '{router_id}': {err}")
        raise RuntimeError(f"Failed executing SNMP walk directly on '{router_id}': {err}")


def _query_single_router_summary(node: Dict[str, Any]) -> FleetSummaryItem:
    """Helper to query status directly from a single router node for batch processing.

    Args:
        node: Router metadata dictionary containing ID, name, URL, etc.

    Returns:
        Populated FleetSummaryItem model.

    Raises:
        None.
    """
    r_id = str(node.get("id", "UNKNOWN"))
    r_name = node.get("name") or r_id
    base_url = str(node.get("url", "")).rstrip("/")

    if not base_url:
        return FleetSummaryItem(
            router_id=r_id,
            name=r_name,
            status="CONFIG_ERROR",
            error="Target URL missing",
        )

    try:
        url = f"{base_url}/api/status"
        headers = get_auth_headers(url)
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        
        telemetry = data.get("telemetry", {})
        leds = data.get("leds", {})
        status_val = telemetry.get("status") or data.get("status") or "OPERATIONAL"

        return FleetSummaryItem(
            router_id=r_id,
            name=r_name,
            status=str(status_val).upper(),
            telemetry=telemetry,
            leds=leds,
        )
    except Exception as err:
        logger.warning(f"Batch status check failed for router '{r_id}' ({base_url}): {err}")
        return FleetSummaryItem(
            router_id=r_id,
            name=r_name,
            status="UNREACHABLE",
            error=str(err),
        )


def fetch_fleet_summary(
    page_size: int = 10,
    page_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetches status telemetry summaries across fleet router nodes in parallel with cursor-based pagination.

    Args:
        page_size: Maximum number of router node summaries per page batch (default: 10, max: 50).
        page_token: Opaque base64 cursor token string indicating starting offset for the next page.

    Returns:
        Dictionary payload adhering to FleetSummaryResponse model.

    Raises:
        RuntimeError: If retrieving fleet registry fails.
    """
    import base64
    from concurrent.futures import ThreadPoolExecutor

    fleet = fetch_fleet_data()
    total_count = len(fleet)

    # Validate and cap page size
    effective_page_size = max(1, min(page_size, 50))

    # Parse cursor offset from page_token
    start_index = 0
    if page_token and page_token.strip():
        try:
            decoded = base64.b64decode(page_token.strip()).decode("utf-8")
            if decoded.startswith("offset:"):
                start_index = int(decoded.split(":", 1)[1])
        except Exception as err:
            logger.warning(f"Invalid page_token '{page_token}' provided; defaulting to start of list: {err}")
            start_index = 0

    if start_index < 0:
        start_index = 0

    page_items = fleet[start_index : start_index + effective_page_size]

    # Execute concurrent parallel HTTP requests across all page items
    summaries: List[FleetSummaryItem] = []
    if page_items:
        workers = min(len(page_items), 20)
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(_query_single_router_summary, item) for item in page_items]
            for fut in futures:
                try:
                    summaries.append(fut.result())
                except Exception as fut_err:
                    logger.error(f"Unexpected error in parallel router summary thread: {fut_err}")

    # Determine next page token
    next_offset = start_index + len(page_items)
    next_page_token: Optional[str] = None
    if next_offset < total_count:
        token_str = f"offset:{next_offset}"
        next_page_token = base64.b64encode(token_str.encode("utf-8")).decode("utf-8")

    response_model = FleetSummaryResponse(
        total_count=total_count,
        page_size=len(summaries),
        next_page_token=next_page_token,
        routers=summaries,
    )

    return response_model.model_dump()

