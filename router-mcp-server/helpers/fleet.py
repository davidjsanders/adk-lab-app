"""Fleet discovery and node communications helpers."""

import json
import logging
import os
from typing import Any, Dict, List

import requests

from .auth import get_auth_headers
from .logger import setup_json_logging

logger = setup_json_logging("router-mcp-server.fleet")

DEFAULT_DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://router-dashboard-cta6n7hkya-uc.a.run.app")


def fetch_fleet_data() -> List[Dict[str, Any]]:
    """Helper to query fleet metadata list from dashboard API or local routers.json fallback.

    Args:
        None.

    Returns:
        List of router node metadata dictionaries.

    Raises:
        None.
    """
    url = f"{DEFAULT_DASHBOARD_URL}/api/routers"
    try:
        headers = get_auth_headers(url)
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            return data.get("routers", [])
        if isinstance(data, list):
            return data
    except Exception as err:
        logger.warning(f"Dashboard URL query to {url} failed ({err}); attempting local routers.json fallback.")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        parent_dir = os.path.dirname(base_dir)
        local_json = os.path.join(parent_dir, "router-dashboard", "routers.json")
        if os.path.exists(local_json):
            try:
                with open(local_json, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as read_err:
                logger.error(f"Failed reading local routers.json: {read_err}")

    return []


def get_router_node(router_id: str) -> Dict[str, Any]:
    """Helper to resolve target router node metadata (URL, control headers, etc.) by ID.

    Args:
        router_id: Unique string ID of target router node.

    Returns:
        Target router node metadata dictionary.

    Raises:
        RuntimeError: If target router ID cannot be found in fleet registration map.
    """
    fleet = fetch_fleet_data()
    for r in fleet:
        if str(r.get("id", "")).upper() == str(router_id).upper():
            return r
    raise RuntimeError(f"Router node '{router_id}' not found in fleet registration.")


def fetch_status_data(router_id: str) -> Dict[str, Any]:
    """Helper to query single router status dict directly from target router node endpoint.

    Args:
        router_id: Unique string ID of target router node.

    Returns:
        Dictionary containing router metadata, telemetry, LED indicators, and logs.

    Raises:
        RuntimeError: If router node metadata lookup or HTTP status query fails.
    """
    node = get_router_node(router_id)
    base_url = str(node.get("url", "")).rstrip("/")
    if not base_url:
        raise RuntimeError(f"Router node '{router_id}' has no configured target URL.")

    url = f"{base_url}/api/status"
    headers = get_auth_headers(url)
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()
