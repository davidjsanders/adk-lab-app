"""GCP Secret Manager Helper Module for Router Operations Dashboard Application.

Manages creation, UUID generation, retrieval, and TTL caching of router control secrets.
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

from helpers.logger import setup_json_logging

logger = setup_json_logging("router-dashboard.secret_manager")

# Cache fetched secret value in memory with TTL
_SECRET_CACHE: Dict[str, Tuple[str, float]] = {}
CACHE_TTL_SECONDS: float = 300.0


def generate_control_uuid() -> str:
    """Generates a cryptographically strong UUID4 string for router control authorization.

    Returns:
        UUID4 string representation.
    """
    return str(uuid.uuid4())


def get_secret_id_for_router(router_id: str) -> str:
    """Constructs standard Secret Manager secret ID string for a given router node.

    Args:
        router_id: Unique router ID string.

    Returns:
        Formatted Secret Manager secret ID string.
    """
    sanitized = router_id.lower().replace("_", "-").replace(" ", "-")
    return f"router-secret-{sanitized}"


def store_router_secret(
    project_id: str,
    secret_id: str,
    secret_payload: str,
) -> Tuple[bool, str]:
    """Creates or updates a secret in GCP Secret Manager with secret_payload string.

    Args:
        project_id: Google Cloud project ID string.
        secret_id: Target Secret Manager secret ID string.
        secret_payload: Plaintext secret payload string.

    Returns:
        Tuple of (success_boolean, status_message_or_secret_name).
    """
    if not HAS_SECRET_MANAGER:
        return False, "google-cloud-secret-manager dependency not available"

    if not project_id or not secret_id or not secret_payload:
        return False, "Missing project_id, secret_id, or secret_payload"

    try:
        client = secretmanager.SecretManagerServiceClient()
        parent = f"projects/{project_id}"
        secret_name = f"{parent}/secrets/{secret_id}"

        # Check if secret exists or create it
        try:
            client.get_secret(request={"name": secret_name})
        except Exception:
            logger.info(f"Secret '{secret_id}' not found. Creating new secret in project '{project_id}'...")
            client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": {
                        "replication": {"automatic": {}},
                    },
                }
            )

        # Add new secret version with payload
        version = client.add_secret_version(
            request={
                "parent": secret_name,
                "payload": {"data": secret_payload.encode("UTF-8")},
            }
        )

        # Update local cache
        _SECRET_CACHE[secret_id] = (secret_payload, time.time())
        logger.info(f"Stored secret version '{version.name}' successfully.")
        return True, version.name
    except Exception as err:
        logger.error(f"Error storing secret '{secret_id}' in Secret Manager: {err}")
        return False, str(err)


def fetch_router_secret(
    project_id: str,
    secret_id: str,
    version_id: str = "latest",
    use_cache: bool = True,
) -> Optional[str]:
    """Retrieves a secret payload string from GCP Secret Manager with caching.

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
        err_str = str(err)
        if "not found" in err_str.lower() or "404" in err_str:
            logger.info(f"Secret '{secret_id}' not found in Secret Manager; falling back to stored password.")
        else:
            logger.error(f"Failed accessing secret '{secret_id}' from Secret Manager: {err}")
        return None
