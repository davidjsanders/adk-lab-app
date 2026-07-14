"""Secret Manager Integration Helper for Router Emulator Application.

Retrieves control authorization secret UUID payload directly from Google Cloud Secret Manager
and performs secure HMAC header authentication verification.
"""

import hmac
import logging
import os
import time
from typing import Dict, Optional, Tuple

from flask import Request

try:
    from google.cloud import secretmanager
    HAS_SECRET_MANAGER = True
except ImportError:
    HAS_SECRET_MANAGER = False

logger = logging.getLogger(__name__)

# Cache fetched secret value in memory with TTL
_SECRET_CACHE: Dict[str, Tuple[str, float]] = {}
CACHE_TTL_SECONDS: float = 300.0


def get_secret_id_for_router(router_id: str) -> str:
    """Constructs standard Secret Manager secret ID string for a given router node.

    Args:
        router_id: Unique router ID string.

    Returns:
        Formatted Secret Manager secret ID string.
    """
    sanitized = router_id.lower().replace("_", "-").replace(" ", "-")
    return f"router-secret-{sanitized}"


def fetch_router_secret(
    project_id: str,
    secret_id: str,
    version_id: str = "latest",
    use_cache: bool = True,
) -> Optional[str]:
    """Retrieves a router control UUID payload from GCP Secret Manager with caching.

    Args:
        project_id: Google Cloud project ID string.
        secret_id: Secret Manager secret ID string.
        version_id: Secret version ID string (defaults to 'latest').
        use_cache: Whether to use in-memory TTL caching.

    Returns:
        Retrieved secret string payload, or None if fetching fails.
    """
    now = time.time()

    if use_cache and secret_id in _SECRET_CACHE:
        cached_val, cached_time = _SECRET_CACHE[secret_id]
        if now - cached_time < CACHE_TTL_SECONDS:
            return cached_val

    if not HAS_SECRET_MANAGER or not project_id or not secret_id:
        return None

    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        secret_val = response.payload.data.decode("UTF-8").strip()

        _SECRET_CACHE[secret_id] = (secret_val, now)
        return secret_val
    except Exception as err:
        logger.error(f"Failed accessing secret '{secret_id}' from Secret Manager: {err}")
        return None


def get_effective_control_password(router_id: str) -> str:
    """Retrieves active router control password UUID from Secret Manager or environment.

    Args:
        router_id: String ID of the targeted router node.

    Returns:
        Active control password string.
    """
    control_pass = os.getenv("CONTROL_PASSWORD", "mock-local-control-password")
    if router_id.startswith("RTR-LOCAL") or not os.getenv("K_SERVICE"):
        return control_pass

    project_id = os.getenv("GCP_PROJECT", os.getenv("PROJECT_ID", ""))
    secret_id = os.getenv("CONTROL_SECRET_ID", "")
    if not secret_id and router_id:
        secret_id = get_secret_id_for_router(router_id)

    if project_id and secret_id:
        sec = fetch_router_secret(project_id, secret_id)
        if sec:
            return sec

    return control_pass


def verify_control_auth(req: Request, control_header_name: str, router_id: str) -> bool:
    """Verifies control password from incoming request header against Secret Manager.

    Args:
        req: Incoming Flask Request object.
        control_header_name: Header key name string (e.g. 'X-Control-Password').
        router_id: Target router ID string.

    Returns:
        True if provided header matches active control secret UUID, False otherwise.
    """
    header_val = req.headers.get(control_header_name, "")
    expected = get_effective_control_password(router_id)
    return hmac.compare_digest(header_val, expected)
