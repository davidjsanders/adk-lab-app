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


DEFAULT_STATIC_FLEET = [
    {
        "id": "RTR-CAN-EAST-01",
        "name": "Canada East Gateway Router",
        "url": "https://router-emulator-rtr-can-east-01-cta6n7hkya-uc.a.run.app",
        "location": "Montréal, QC",
        "purpose": "Central Hub BGP Border Gateway",
        "source": "CLOUDRUN",
        "secret_id": "router-secret-rtr-can-east-01",
    },
    {
        "id": "CAN-NN2-CENTRAL-01",
        "name": "Canada Northeast 2 Router 1",
        "url": "https://router-emulator-can-nn2-central-01-cta6n7hkya-uc.a.run.app",
        "location": "Toronto, ON",
        "purpose": "East Hub BGP Border Gateway",
        "source": "CLOUDRUN",
        "secret_id": "router-secret-can-nn2-central-01",
    },
    {
        "id": "RTR-CAN-EAST-02",
        "name": "Canada Northeast 2 Router 2",
        "url": "https://router-emulator-rtr-can-east-02-cta6n7hkya-uc.a.run.app",
        "location": "Toronto, ON",
        "purpose": "Backup East Hub BGP Border Gateway",
        "source": "CLOUDRUN",
        "secret_id": "router-secret-rtr-can-east-02",
    },
]


def fetch_fleet_data() -> List[Dict[str, Any]]:
    """Helper to query fleet metadata list from dashboard API or direct GCP Cloud Run discovery fallback.

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
        if isinstance(data, dict) and "routers" in data:
            return data["routers"]
        if isinstance(data, list):
            return data
    except Exception as err:
        logger.warning(f"Dashboard URL query to {url} failed ({err}); attempting fallback inventory assembly.")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parent_dir = os.path.dirname(base_dir)
    local_json = os.path.join(parent_dir, "router-dashboard", "routers.json")
    loaded_nodes: List[Dict[str, Any]] = []
    if os.path.exists(local_json):
        try:
            with open(local_json, "r", encoding="utf-8") as f:
                loaded_nodes = json.load(f)
        except Exception as read_err:
            logger.error(f"Failed reading local routers.json: {read_err}")

    load_cloud_fleet = os.getenv("LOAD_CLOUD_FLEET", "true").strip().lower() in ("true", "1", "yes")
    if load_cloud_fleet:
        try:
            mod = _load_dashboard_cloud_run_module()
            cr_nodes = mod.discover_cloud_run_routers()
            known_ids = {node["id"] for node in loaded_nodes if isinstance(node, dict) and "id" in node}
            for cr_node in cr_nodes:
                cr_id = cr_node["id"]
                if cr_id not in known_ids:
                    loaded_nodes.append(cr_node)
                    known_ids.add(cr_id)
            logger.info(f"Direct GCP Cloud Run discovery loaded {len(cr_nodes)} cloud nodes (LOAD_CLOUD_FLEET=true).")
        except Exception as cr_err:
            logger.warning(f"Direct GCP Cloud Run discovery failed ({cr_err}); using static fallback metadata.")
            known_ids = {node["id"] for node in loaded_nodes if isinstance(node, dict) and "id" in node}
            for default_node in DEFAULT_STATIC_FLEET:
                if default_node["id"] not in known_ids:
                    loaded_nodes.append(default_node)

    return loaded_nodes


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


def _load_dashboard_cloud_run_module():
    import sys
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parent_dir = os.path.dirname(base_dir)
    dash_dir = os.path.join(parent_dir, "router-dashboard")

    if dash_dir not in sys.path:
        sys.path.insert(0, dash_dir)

    saved_modules = {k: v for k, v in list(sys.modules.items()) if k == "helpers" or k.startswith("helpers.")}
    for k in saved_modules:
        del sys.modules[k]

    try:
        from helpers import cloud_run
        return cloud_run
    finally:
        for k in list(sys.modules.keys()):
            if k == "helpers" or k.startswith("helpers."):
                del sys.modules[k]
        sys.modules.update(saved_modules)


def dispatch_register_router(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Registers a new router node or deploys a new Cloud Run container service.

    Args:
        payload: Dictionary containing router registration parameters (id, name, location, purpose, etc.).

    Returns:
        Dictionary containing operational response status and registration metadata.

    Raises:
        RuntimeError: If registration request fails.
    """
    url = f"{DEFAULT_DASHBOARD_URL}/api/routers"
    try:
        headers = get_auth_headers(url)
        headers["Content-Type"] = "application/json"
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except Exception as err:
        logger.warning(f"Dashboard HTTP query for register router failed ({err}); attempting direct GCP API fallback...")
        try:
            mod = _load_dashboard_cloud_run_module()
            r_id = payload.get("id", "")
            r_name = payload.get("name", "")
            r_loc = payload.get("location", "")
            r_purp = payload.get("purpose", "")
            is_cr = payload.get("deploy_cloud_run") or payload.get("deploy_cloudrun")

            if is_cr:
                ok, msg, assigned_url = mod.deploy_router_to_cloud_run(r_id, r_name, r_loc, r_purp)
                if ok:
                    return {"status": "SUCCESS", "message": msg, "url": assigned_url}
                raise RuntimeError(msg)
            else:
                return {"status": "SUCCESS", "message": f"Local test router '{r_id}' registered successfully."}
        except Exception as fallback_err:
            logger.error(f"Error registering router node '{payload.get('id')}': {fallback_err}")
            raise RuntimeError(f"Failed registering router node '{payload.get('id')}': {fallback_err}")


def dispatch_clone_router(
    source_router_id: str,
    new_router_id: str,
    new_name: Optional[str] = None,
    location: Optional[str] = None,
    purpose: Optional[str] = None,
    deploy_cloud_run: Optional[bool] = None,
) -> Dict[str, Any]:
    """Clones an existing router node configuration with customized parameter overrides.

    Args:
        source_router_id: Target router node ID to copy properties from.
        new_router_id: Unique string ID for the new cloned router instance.
        new_name: Optional display name for cloned router (defaults to 'Copy of <source.name>').
        location: Optional physical/cloud location string description.
        purpose: Optional operational role/purpose description.
        deploy_cloud_run: Optional boolean flag to deploy a Cloud Run container service.

    Returns:
        Dictionary containing registration result and status payload.

    Raises:
        RuntimeError: If source router lookup or registration dispatch fails.
    """
    source_node = get_router_node(source_router_id)
    is_cloud_run = deploy_cloud_run if deploy_cloud_run is not None else (source_node.get("source") == "CLOUDRUN" or "a.run.app" in source_node.get("url", ""))

    payload = {
        "id": new_router_id.strip(),
        "name": new_name.strip() if new_name else f"Copy of {source_node.get('name', source_router_id)}",
        "location": location.strip() if location else source_node.get("location", "Cloud Data Center"),
        "purpose": purpose.strip() if purpose else source_node.get("purpose", "Edge Core Router"),
        "manufacturer": source_node.get("manufacturer", "Cisco Systems"),
        "model": source_node.get("model", "Nexus 9300-EX"),
        "control_header": source_node.get("control_header", "X-Control-Password"),
        "deploy_cloud_run": is_cloud_run,
        "deploy_cloudrun": is_cloud_run,
        "url": source_node.get("url", "") if not is_cloud_run else "",
    }

    logger.info(f"Cloning router node '{source_router_id}' to '{new_router_id}' (Cloud Run: {is_cloud_run})...")
    return dispatch_register_router(payload)


def dispatch_delete_router(router_id: str) -> Dict[str, Any]:
    """Tears down a router node (deleting its Cloud Run service, Secret Manager key, and registry record).

    Args:
        router_id: Unique string ID of target router node.

    Returns:
        Dictionary containing deletion response status and confirmation message.

    Raises:
        RuntimeError: If HTTP deletion request fails.
    """
    url = f"{DEFAULT_DASHBOARD_URL}/api/routers/{router_id}"
    try:
        headers = get_auth_headers(url)
        resp = requests.delete(url, headers=headers, timeout=45)
        resp.raise_for_status()
        return resp.json()
    except Exception as err:
        logger.warning(f"Dashboard HTTP query for delete router failed ({err}); attempting direct GCP API fallback...")
        try:
            mod = _load_dashboard_cloud_run_module()
            ok, msg = mod.delete_cloud_run_router(router_id)
            if ok:
                return {"status": "SUCCESS", "message": msg}
            raise RuntimeError(msg)
        except Exception as fallback_err:
            logger.error(f"Error tearing down router node '{router_id}': {fallback_err}")
            raise RuntimeError(f"Failed deleting router node '{router_id}': {fallback_err}")


def dispatch_redeploy_routers(router_ids: List[str]) -> Dict[str, Any]:
    """Triggers an immediate Cloud Run container redeployment for target router nodes.

    Args:
        router_ids: List of target router string IDs.

    Returns:
        Dictionary containing redeployment execution status and results per node.

    Raises:
        RuntimeError: If redeploy request fails.
    """
    url = f"{DEFAULT_DASHBOARD_URL}/api/proxy/redeploy"
    try:
        headers = get_auth_headers(url)
        headers["Content-Type"] = "application/json"
        resp = requests.post(url, headers=headers, json={"router_ids": router_ids}, timeout=90)
        resp.raise_for_status()
        return resp.json()
    except Exception as err:
        logger.error(f"Error redeploying router nodes {router_ids}: {err}")
        raise RuntimeError(f"Failed redeploying router nodes {router_ids}: {err}")
