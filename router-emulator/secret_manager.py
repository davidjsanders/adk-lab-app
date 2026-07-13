"""Secret Manager integration module for Router Emulator Application.

Retrieves router control password UUID payload directly from Google Cloud Secret Manager.
"""

import logging
import time
from typing import Dict, Optional, Tuple
import uuid

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
