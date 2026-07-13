"""Router Emulator Flask Application.

This application emulates a physical router with status LEDs, LCD display,
and command interface protected by Secret Manager header authorization.
"""

import hmac
import logging
import os
from typing import Dict, Tuple, Union

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, Response

from classes import RouterState, SNMPAgent
from helpers import verify_control_auth

# Load environment configuration
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Initialize hardware router state instance from environment variables
router = RouterState(
    router_id=os.getenv("ROUTER_ID", "RTR-CORE-01"),
    location=os.getenv("ROUTER_LOCATION", "Data Center Alpha - Rack 12B"),
    purpose=os.getenv("ROUTER_PURPOSE", "Primary Edge Core Router"),
    manufacturer=os.getenv("MANUFACTURER_ID", "CISCO-NEXUS-9000-X"),
    firmware_version=os.getenv("FIRMWARE_VERSION", "v4.18.2-LTS"),
)

# Control Password & Header Settings
CONTROL_HEADER: str = os.getenv("CONTROL_HEADER", "X-Control-Password")

# SNMP Emulation Settings
SNMP_ENABLED: bool = os.getenv("SNMP_ENABLED", "true").lower() == "true"
SNMP_COMMUNITY: str = os.getenv("SNMP_COMMUNITY", "public")


@app.before_request
def touch_router_activity() -> None:
    """Updates router node activity timestamp on every incoming request."""
    router.touch_activity()


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


@app.route("/")
def index() -> str:
    """Renders the single page web application interface.

    Returns:
        HTML content of the router visualizer index page.
    """
    return render_template(
        "index.html",
        router_id=router.router_id,
        router_location=router.location,
        router_purpose=router.purpose,
        manufacturer_id=router.manufacturer,
        firmware_version=router.firmware_version,
        control_header=CONTROL_HEADER,
    )


@app.route("/compact")
@app.route("/widget")
def compact() -> str:
    """Renders the compact router LEDs standalone view for multi-router dashboards.

    Returns:
        HTML content of the compact router visualizer page.
    """
    return render_template(
        "compact.html",
        router_id=router.router_id,
        router_location=router.location,
        router_purpose=router.purpose,
        manufacturer_id=router.manufacturer,
        firmware_version=router.firmware_version,
        control_header=CONTROL_HEADER,
    )


@app.route("/api/status", methods=["GET"])
def get_status() -> Response:
    """Fetches full telemetry, metadata, LED state, and logs for the router.

    Returns:
        JSON response with router metadata, LED states, uptime, and logs.
    """
    data = router.to_telemetry_dict()
    data["metadata"]["snmp"] = {
        "enabled": SNMP_ENABLED,
        "community": SNMP_COMMUNITY,
        "walk_endpoint": "/snmp/walk",
        "get_endpoint": "/snmp/get",
    }
    return jsonify(data)


@app.route("/snmp/walk", methods=["GET"])
@app.route("/snmp/get", methods=["GET"])
def http_snmp_emulator() -> Union[Response, str, Tuple[Response, int]]:
    """Emulates snmpwalk and snmpget commands via single HTTP ingress port.

    Query Parameters:
        community: SNMP community string (default: public).
        oid: Filter OID prefix (e.g. 1.3.6.1.2.1.1 or 1.3.6.1.2.1.1.5.0).
        format: Output format ('text' for snmpwalk CLI style, 'json' for JSON).

    Returns:
        Formatted snmpwalk plain text or JSON output.
    """
    if not SNMP_ENABLED:
        return jsonify({"error": "SNMP Disabled", "message": "SNMP emulation is disabled"}), 403

    req_community = request.args.get("community", "public")
    if not hmac.compare_digest(req_community, SNMP_COMMUNITY):
        return jsonify({"error": "Unauthorized", "message": f"Invalid SNMP community '{req_community}'"}), 401

    mib = SNMPAgent.compile_mib_tree(router)
    filter_oid_str = request.args.get("oid", "").strip()

    if filter_oid_str:
        filter_tuple = SNMPAgent.oid_to_tuple(filter_oid_str)
        mib = {
            k: v for k, v in mib.items()
            if k[:len(filter_tuple)] == filter_tuple
        }

    output_format = request.args.get("format", "").lower()
    accept_header = request.headers.get("Accept", "")

    if output_format == "text" or "text/plain" in accept_header:
        text_output = SNMPAgent.format_snmpwalk_output(mib)
        return Response(text_output, mimetype="text/plain")

    formatted_json = {
        item["oid"]: {
            "name": item["name"],
            "type": item["type"],
            "value": item["value"],
        }
        for _, item in sorted(mib.items())
    }

    return jsonify({
        "status": "SUCCESS",
        "router_id": router.router_id,
        "community": req_community,
        "count": len(formatted_json),
        "mib_objects": formatted_json,
    })


@app.route("/api/snmp", methods=["GET"])
def get_snmp_tree() -> Response:
    """Provides a REST API representation of all MIB-II SNMP OID values.

    Returns:
        JSON object containing formatted MIB OIDs and values.
    """
    mib = SNMPAgent.compile_mib_tree(router)
    formatted_json = {
        item["oid"]: {
            "name": item["name"],
            "type": item["type"],
            "value": item["value"],
        }
        for _, item in sorted(mib.items())
    }

    return jsonify({
        "snmp_status": "ENABLED" if SNMP_ENABLED else "DISABLED",
        "community": SNMP_COMMUNITY,
        "count": len(formatted_json),
        "mib_tree": formatted_json,
    })


@app.route("/api/command", methods=["POST"])
def execute_command() -> Union[Response, Tuple[Response, int]]:
    """Receives and processes operational commands for the router emulator.

    Returns:
        JSON response indicating outcome of command execution.

    Raises:
        401 Unauthorized if missing or invalid control header.
        400 Bad Request if missing command or unrecognized command.
    """
    if not verify_control_auth(request, CONTROL_HEADER, router.router_id):
        router.add_log(f"Unauthorized access attempt to control command API from {request.remote_addr}", "WARN")
        return jsonify({
            "error": "Unauthorized",
            "message": f"Invalid or missing header '{CONTROL_HEADER}'",
        }), 401

    payload = request.get_json(silent=True) or {}
    command = payload.get("command", "").strip()
    params = payload.get("parameters", {})

    if not command:
        return jsonify({"error": "Bad Request", "message": "Missing 'command' parameter"}), 400

    res_data, status_code = router.execute_command(command, params, request.remote_addr)
    return jsonify(res_data), status_code


@app.route("/health", methods=["GET"])
def health_check() -> Tuple[Response, int]:
    """Provides a health check endpoint for Cloud Run container probes.

    Returns:
        JSON response with system health status.
    """
    return jsonify({"status": "healthy", "router_id": router.router_id}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="127.0.0.1", port=port, debug=True)
