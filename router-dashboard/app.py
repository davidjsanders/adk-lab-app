"""Router Fleet Operations Dashboard Flask Application.

Provides multi-router fleet visualization, auto-discovery of Cloud Run instances,
OIDC IAM proxying of telemetry commands, and hardware visualizers.
"""

import logging
import os
from typing import Any, Dict, List, Tuple, Union

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, Response
import requests

from classes import RouterNode, RouterRegistry
from helpers import (
    build_proxy_headers,
    deploy_router_to_cloud_run,
    fetch_router_secret,
    generate_control_uuid,
    get_secret_id_for_router,
    store_router_secret,
)

# Load environment configuration
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DASHBOARD_NAME: str = os.getenv("DASHBOARD_NAME", "Global Router Operations Center")
ROUTERS_CONFIG_FILE: str = os.getenv("ROUTERS_CONFIG_FILE", "routers.json")
GCP_PROJECT: str = os.getenv("GCP_PROJECT", "agentspace-argolis-demo")
GCP_REGION: str = os.getenv("GCP_REGION", "us-central1")

# Initialize central fleet registry manager
registry = RouterRegistry(config_path=ROUTERS_CONFIG_FILE, project_id=GCP_PROJECT, region=GCP_REGION)


@app.after_request
def add_security_headers(response: Response) -> Response:
    """Adds security headers to HTTP responses.

    Args:
        response: Incoming Flask Response object.

    Returns:
        Flask Response object with hardened security headers.
    """
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline'; "
        "frame-ancestors *;"
    )
    return response


POLLING_INTERVAL_MS: int = int(os.getenv("POLLING_INTERVAL_MS", "1500"))


@app.route("/")
def index() -> str:
    """Renders the single page web application interface.

    Returns:
        HTML content of the router visualizer index page.
    """
    return render_template(
        "index.html",
        dashboard_name=DASHBOARD_NAME,
        polling_interval_ms=POLLING_INTERVAL_MS
    )


@app.route("/api/routers", methods=["GET"])
def get_routers() -> Response:
    """Returns the complete list of registered and auto-discovered router nodes.

    Returns:
        JSON response with count and array of router node objects.
    """
    routers = registry.get_all_routers()
    return jsonify({
        "count": len(routers),
        "routers": [r.to_dict() for r in routers],
    })


@app.route("/api/routers", methods=["POST"])
def add_router() -> Tuple[Response, int]:
    """Registers a new router node or deploys a new instance to Cloud Run.

    Payload Example:
        {
            "id": "RTR-US-EAST-01",
            "name": "US East Router",
            "url": "https://router-emulator-rtr-us-east-01-xxx.a.run.app",
            "location": "New York, NY",
            "purpose": "Border Gateway",
            "deploy_cloud_run": true
        }

    Returns:
        JSON response with operational status.

    Raises:
        400 Bad Request if missing required fields or deployment fails.
    """
    payload = request.get_json(silent=True) or {}
    router_id = payload.get("id", "").strip()
    name = payload.get("name", "").strip() or router_id
    url = payload.get("url", "").strip()
    location = payload.get("location", "Remote Datacenter").strip()
    purpose = payload.get("purpose", "Edge Core Router").strip()
    deploy_cr = bool(payload.get("deploy_cloud_run", payload.get("deploy_cloudrun", False)))
    control_password = payload.get("control_password", "").strip()
    control_header = payload.get("control_header", "X-Control-Password").strip() or "X-Control-Password"

    if not router_id:
        return jsonify({"error": "Bad Request", "message": "Missing required field 'id'"}), 400

    secret_id = get_secret_id_for_router(router_id)

    # 1. Cloud Run Deployment Path
    if deploy_cr:
        if not control_password:
            control_password = generate_control_uuid()

        success, res_val = deploy_router_to_cloud_run(
            router_id=router_id,
            location=location,
            purpose=purpose,
            control_password=control_password,
            control_header=control_header,
        )

        if not success:
            return jsonify({"error": "Cloud Run Deployment Error", "message": res_val}), 400

        url = res_val
        source = "CLOUDRUN"
    else:
        if not url:
            return jsonify({"error": "Bad Request", "message": "Missing required field 'url'"}), 400
        source = "MANUAL"

        if control_password:
            store_router_secret(GCP_PROJECT, secret_id, control_password)

    node = RouterNode(
        id=router_id,
        name=name,
        url=url,
        location=location,
        purpose=purpose,
        secret_id=secret_id,
        control_header=control_header,
        control_password=control_password,
        source=source,
    )

    registry.register_router(node)
    return jsonify({
        "status": "SUCCESS",
        "message": f"Router node '{router_id}' registered successfully",
        "url": url,
    }), 200


@app.route("/api/routers/<router_id>", methods=["PUT"])
def update_router(router_id: str) -> Tuple[Response, int]:
    """Updates configuration parameters for an existing registered router node.

    Payload Example:
        {
            "name": "Canada East Core Router",
            "location": "Montréal, QC",
            "purpose": "Primary BGP Gateway",
            "manufacturer": "Cisco Systems",
            "model": "Nexus 9300-EX",
            "control_password": "new_secret_password",
            "redeploy_cloud_run": true
        }

    Returns:
        JSON response with updated router configuration.
    """
    node = registry.get_router_by_id(router_id)
    if not node:
        return jsonify({"error": "Not Found", "message": f"Router node '{router_id}' not found"}), 404

    payload = request.get_json(silent=True) or {}
    if "name" in payload: node.name = payload["name"].strip()
    if "location" in payload: node.location = payload["location"].strip()
    if "purpose" in payload: node.purpose = payload["purpose"].strip()
    if "manufacturer" in payload: node.manufacturer = payload["manufacturer"].strip()
    if "model" in payload: node.model = payload["model"].strip()
    if "control_password" in payload and payload["control_password"].strip():
        node.control_password = payload["control_password"].strip()

    redeploy = bool(payload.get("redeploy_cloud_run", False))
    redeploy_msg = ""

    if redeploy:
        logger.info(f"Redeploying router '{router_id}' after settings update...")
        success, res_val = deploy_router_to_cloud_run(
            router_id=node.id,
            location=node.location,
            purpose=node.purpose,
            control_password=node.control_password,
            control_header=node.control_header,
        )
        if success:
            node.url = res_val
            redeploy_msg = f" and redeployed to Cloud Run ({res_val})"
        else:
            logger.error(f"Cloud Run redeployment failed for {router_id}: {res_val}")

    registry.register_router(node)
    return jsonify({
        "status": "SUCCESS",
        "message": f"Router '{router_id}' settings updated{redeploy_msg}",
        "router": node.to_dict(),
    }), 200


@app.route("/api/routers/<router_id>", methods=["DELETE"])
def delete_router(router_id: str) -> Tuple[Response, int]:
    """Removes a router node from local registration.

    Args:
        router_id: Unique string ID of router node.

    Returns:
        JSON response with operational status.
    """
    removed = registry.remove_router(router_id)
    if not removed:
        return jsonify({"error": "Not Found", "message": f"Router '{router_id}' not found in local registry"}), 404

    return jsonify({"status": "SUCCESS", "message": f"Router node '{router_id}' removed"}), 200


@app.route("/api/proxy/status", methods=["GET"])
def proxy_status() -> Tuple[Response, int]:
    """Proxies status telemetry query to a targeted router emulator instance.

    Query Parameters:
        router_id: Target router ID string.

    Returns:
        JSON response with router status and telemetry data.
    """
    router_id = request.args.get("router_id", "").strip()
    target_node = registry.get_router_by_id(router_id)

    if not target_node:
        return jsonify({"error": "Not Found", "message": f"Router '{router_id}' not found"}), 404

    target_url = f"{target_node.url}/api/status"
    try:
        headers = build_proxy_headers(target_url)
        res = requests.get(target_url, headers=headers, timeout=5.0)
        return jsonify(res.json()), res.status_code
    except Exception as err:
        res_code = getattr(res, "status_code", "N/A") if "res" in locals() else "N/A"
        res_text = getattr(res, "text", "")[:300] if "res" in locals() else ""
        logger.error(f"Failed connecting to router {router_id} at {target_url} (HTTP {res_code}): {err}. Body: {res_text}")
        return jsonify({
            "error": "Offline",
            "message": f"Failed connecting to router {router_id}: {str(err)}",
            "telemetry": {
                "status": "OFFLINE",
                "uptime_seconds": 0,
                "booting": False,
            },
            "leds": {
                "power": "off",
                "online": "off",
                "upstream": "off",
                "lan1": "off",
                "lan2": "off",
                "lan3": "off",
                "lan4": "off",
                "send": "off",
                "receive": "off",
            }
        }), 200


@app.route("/api/proxy/redeploy", methods=["POST"])
def proxy_redeploy() -> Tuple[Response, int]:
    """Redeploys targeted router node(s) to Google Cloud Run from the pre-built image tag.

    Payload Example:
        {
            "router_id": "RTR-CAN-EAST-01",
            "router_ids": ["RTR-CAN-EAST-01", "RTR-CAN-EAST-02"]
        }

    Returns:
        JSON response with deployment status and active service URL(s).
    """
    payload = request.get_json(silent=True) or {}
    router_ids = payload.get("router_ids", [])
    if not router_ids and payload.get("router_id"):
        router_ids = [payload.get("router_id").strip()]

    if not router_ids:
        return jsonify({"error": "Bad Request", "message": "Missing required field 'router_id' or 'router_ids'"}), 400

    results = {}
    overall_success = True

    for r_id in router_ids:
        target_node = registry.get_router_by_id(r_id)
        if not target_node:
            results[r_id] = {"error": "Not Found", "message": f"Router node '{r_id}' not found"}
            overall_success = False
            continue

        logger.info(f"Triggering Cloud Run redeployment for router '{r_id}'...")
        success, res_val = deploy_router_to_cloud_run(
            router_id=target_node.id,
            location=target_node.location,
            purpose=target_node.purpose,
            control_password=target_node.control_password,
            control_header=target_node.control_header,
        )

        if not success:
            results[r_id] = {"error": "Redeployment Failed", "message": res_val}
            overall_success = False
        else:
            target_node.url = res_val
            registry.register_router(target_node)
            results[r_id] = {
                "status": "SUCCESS",
                "message": f"Router node '{r_id}' redeployed successfully to Cloud Run",
                "url": res_val,
            }

    if len(router_ids) == 1:
        single_res = results[router_ids[0]]
        status_code = 200 if "error" not in single_res else 500
        return jsonify(single_res), status_code

    return jsonify({
        "status": "SUCCESS" if overall_success else "PARTIAL_SUCCESS",
        "results": results
    }), 200


@app.route("/api/proxy/command", methods=["POST"])
def proxy_command() -> Tuple[Response, int]:
    """Proxies an operational control command to targeted router emulator instance(s).

    Payload Example:
        {
            "router_id": "RTR-US-EAST-01",
            "router_ids": ["RTR-US-EAST-01", "RTR-CAN-EAST-02"],
            "command": "bgp_reset",
            "parameters": {}
        }

    Returns:
        JSON response returned by the targeted router emulator instance(s).
    """
    payload = request.get_json(silent=True) or {}
    command = payload.get("command", "").strip()
    params = payload.get("parameters", {})

    router_ids = payload.get("router_ids", [])
    if not router_ids and payload.get("router_id"):
        router_ids = [payload.get("router_id").strip()]

    if not router_ids or not command:
        return jsonify({"error": "Bad Request", "message": "Missing 'router_id'/'router_ids' or 'command'"}), 400

    results = {}
    overall_success = True

    for r_id in router_ids:
        target_node = registry.get_router_by_id(r_id)
        if not target_node:
            results[r_id] = {"error": "Not Found", "message": f"Target router '{r_id}' is unregistered"}
            overall_success = False
            continue

        target_url = f"{target_node.url}/api/command"
        header_name = target_node.control_header
        secret_id = target_node.secret_id or get_secret_id_for_router(r_id)

        # Fetch active control secret UUID from Secret Manager, falling back to stored password
        password = fetch_router_secret(GCP_PROJECT, secret_id) or target_node.control_password

        try:
            headers = build_proxy_headers(target_url, {
                "Content-Type": "application/json",
                header_name: password,
            })
            res = requests.post(target_url, json={"command": command, "parameters": params}, headers=headers, timeout=5.0)
            results[r_id] = res.json()
        except Exception as err:
            logger.error(f"Failed proxy command to {target_url}: {err}")
            results[r_id] = {"error": "Proxy Error", "message": str(err)}
            overall_success = False

    if len(router_ids) == 1:
        single_res = results[router_ids[0]]
        status_code = 200 if "error" not in single_res else 400
        return jsonify(single_res), status_code

    return jsonify({
        "status": "SUCCESS" if overall_success else "PARTIAL_SUCCESS",
        "command": command,
        "results": results
    }), 200


@app.route("/api/proxy/snmp", methods=["GET"])
def proxy_snmp() -> Tuple[Response, int]:
    """Proxies an SNMP walk or get query to a targeted router emulator instance over HTTP.

    Query Parameters:
        router_id: Target router ID string.
        oid: Optional OID filter string.
        format: 'text' or 'json'.

    Returns:
        Formatted SNMP MIB response.
    """
    router_id = request.args.get("router_id", "").strip()
    oid = request.args.get("oid", "").strip()
    output_format = request.args.get("format", "json").strip()

    target_node = registry.get_router_by_id(router_id)
    if not target_node:
        return jsonify({"error": "Not Found", "message": f"Router '{router_id}' not found"}), 404

    target_url = f"{target_node.url}/snmp/walk?oid={oid}&format={output_format}"

    try:
        headers = build_proxy_headers(target_url)
        res = requests.get(target_url, headers=headers, timeout=5.0)
        if output_format == "text":
            return Response(res.text, mimetype="text/plain", status=res.status_code)
        return jsonify(res.json()), res.status_code
    except Exception as err:
        return jsonify({
            "error": "Bad Gateway",
            "message": f"Failed querying SNMP from router {router_id}: {str(err)}",
        }), 502


@app.route("/health", methods=["GET"])
def health_check() -> Tuple[Response, int]:
    """Provides a health check endpoint for Cloud Run container probes.

    Returns:
        JSON response with service health status.
    """
    return jsonify({"status": "healthy", "service": "router-dashboard"}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="127.0.0.1", port=port, debug=True)
